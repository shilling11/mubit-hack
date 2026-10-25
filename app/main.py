"""Redress API. Run with: uvicorn app.main:app --port 8000   (no --reload when demoing)"""
import os
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app import db, demo
from app.capture import ingest, stt
from app.config import MUBIT_API_KEY, MUBIT_BASE_URL, MUBIT_MODEL, DEEPGRAM_API_KEY, REVIEW_REASONING_EFFORT
from app.eval import runner
from app.learning import corrections, playbook, test_on_archive
from app.llm.mubit_client import MubitError
from app.review import service
from app.review.spec import items_by_id, scorecard

_work = ThreadPoolExecutor(max_workers=2, thread_name_prefix="call")


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init()
    # Runs can belong to other processes (scripts), so only clear clearly stale ones.
    db.execute("UPDATE runs SET status = 'interrupted' WHERE status = 'running' AND created_at < ?", (time.time() - 1800,))
    yield


app = FastAPI(title="Redress", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("REDRESS_WEB_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ───────────────────────────────────────────────────────────────────
class Utterance(BaseModel):
    speaker: str = Field(pattern="^(agent|customer)$")
    text: str
    start_s: float
    end_s: float | None = None


class ImportCall(BaseModel):
    id: str | None = None
    agent_name: str = ""
    utterances: list[Utterance]


class ImportIn(BaseModel):
    split: str = Field(default="practice", pattern="^(practice|heldout|live)$")
    review: bool = True
    calls: list[ImportCall]


class ItemAnswer(BaseModel):
    id: str
    answer: str = Field(pattern="^(yes|no|na|unsure)$")
    reason: str = ""


class EvaluationIn(BaseModel):
    review_id: int | None = None
    analyst: str = "analyst"
    items: list[ItemAnswer] = []
    comments: str = ""


class EvalIn(BaseModel):
    repeats: int = Field(default=3, ge=1, le=5)
    versions: list[int] | None = None
    split: str = "heldout"


# ── Helpers ──────────────────────────────────────────────────────────────────
def _404(fn, *args, **kw):
    try:
        return fn(*args, **kw)
    except KeyError as exc:
        raise HTTPException(404, f"Not found: {exc}") from exc


def _call_view(call_id: str) -> dict:
    call = db.one("SELECT * FROM calls WHERE id = ?", (call_id,))
    if not call:
        raise HTTPException(404, call_id)
    review = service.latest_review(call_id)
    defs = items_by_id()
    if review and review.get("items_json"):
        review["items"] = [{**review["items_json"][i], "label": d["label"], "kind": d["kind"], "weight": d["weight"],
                            "basis": d["basis"]} for i, d in defs.items()]
    return {
        **call,
        "utterances": service.utterances(call_id),
        "review": review,
        "queue": db.one("SELECT * FROM queue WHERE call_id = ?", (call_id,)),
        "evaluation": db.one("SELECT * FROM evaluations WHERE call_id = ? ORDER BY id DESC LIMIT 1", (call_id,)),
    }


def _process_upload(call_id: str, mimetype: str) -> None:
    try:
        ingest.transcribe_call(call_id, mimetype)
        service.review_call(call_id)
    except (stt.STTError, MubitError, ValueError) as exc:
        db.update("calls", {"id": call_id}, {"status": "failed", "error": str(exc)[:500]})


def _review_bg(call_id: str, version: int | None = None) -> None:
    try:
        service.review_call(call_id, version)
    except Exception as exc:
        db.update("calls", {"id": call_id}, {"status": "failed", "error": str(exc)[:500]})


# ── Status ───────────────────────────────────────────────────────────────────
@app.get("/api/status")
def status():
    t = db.one("SELECT COUNT(*) AS calls, SUM(ok = 0) AS errors FROM traces") or {}
    ex = db.one("SELECT COUNT(*) AS n FROM traces WHERE task = 'review.call' AND record_mode = 'full' AND ok = 1") or {}
    return {
        "training_examples_sent": ex.get("n") or 0,
        "mubit": {"base_url": MUBIT_BASE_URL, "key_set": bool(MUBIT_API_KEY), "model": MUBIT_MODEL,
                  "reasoning_effort": REVIEW_REASONING_EFFORT},
        "deepgram_key_set": bool(DEEPGRAM_API_KEY),
        "playbook_version": playbook.latest_version(),
        "pending_corrections": len(playbook.pending_corrections()),
        "mubit_calls": t.get("calls") or 0,
        "mubit_errors": t.get("errors") or 0,
    }


@app.get("/api/scorecard")
def get_scorecard():
    return scorecard()


# ── Calls ────────────────────────────────────────────────────────────────────
@app.post("/api/calls")
async def upload_call(audio: UploadFile = File(...), agent_name: str = Form(""), customer_name: str = Form("")):
    data = await audio.read()
    if not data:
        raise HTTPException(400, "empty recording")
    mimetype = audio.content_type or "audio/webm"
    call_id = ingest.save_recording(data, mimetype, agent_name, customer_name)
    _work.submit(_process_upload, call_id, mimetype)
    return {"call_id": call_id}


@app.post("/api/calls/import")
def import_calls(body: ImportIn):
    ids = []
    for c in body.calls:
        utts = [u.model_dump() for u in c.utterances]
        ids.append(ingest.create_call(utts, source="synthetic" if body.split != "live" else "upload",
                                      split=body.split, agent_name=c.agent_name, call_id=c.id))
    if body.review:
        for cid in ids:
            _work.submit(_review_bg, cid)
    return {"count": len(ids), "call_ids": ids}


@app.post("/api/demo/scripts/{script_id}")
def load_demo_call(script_id: str, review: bool = True):
    """Load a demo script as a text call (rehearsal / fallback when audio fails)."""
    try:
        cid = demo.load_script(script_id)
    except StopIteration as exc:
        raise HTTPException(404, script_id) from exc
    if review:
        _work.submit(_review_bg, cid)
    return {"call_id": cid}


@app.get("/api/calls")
def list_calls(split: str | None = None, limit: int = 200):
    sql = ("SELECT c.id, c.source, c.split, c.agent_name, c.duration_s, c.status, c.created_at, q.kind AS queue_kind, "
           "q.audit, r.score, r.pass, r.risk_tier, r.critical_fails FROM calls c "
           "LEFT JOIN queue q ON q.call_id = c.id "
           "LEFT JOIN reviews r ON r.id = q.review_id ")
    params: tuple = ()
    if split:
        sql += "WHERE c.split = ? "
        params = (split,)
    return db.query(sql + "ORDER BY c.created_at DESC LIMIT ?", params + (max(1, min(limit, 1000)),))


@app.get("/api/calls/{call_id}")
def get_call(call_id: str):
    return _call_view(call_id)


@app.get("/api/calls/{call_id}/audio")
def get_audio(call_id: str):
    call = db.one("SELECT audio_path FROM calls WHERE id = ?", (call_id,))
    if not call or not call.get("audio_path") or not os.path.exists(call["audio_path"]):
        raise HTTPException(404, "no audio for this call")
    return FileResponse(call["audio_path"])


@app.post("/api/calls/{call_id}/review")
def rereview(call_id: str, playbook_version: int | None = None):
    """Re-score a call synchronously (e.g. to show base vs latest playbook side by side)."""
    try:
        r = _404(service.review_call, call_id, playbook_version,
                 update_queue=playbook_version is None, run_id=None if playbook_version is None else "compare")
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if r.get("error"):
        raise HTTPException(502, r["error"])
    return r


@app.post("/api/calls/{call_id}/utterances/{idx}/flip")
def flip_line(call_id: str, idx: int):
    """Fix one mislabelled line. Re-score afterwards with POST /api/calls/{id}/review."""
    return {"idx": idx, "speaker": _404(ingest.flip_speaker, call_id, idx)}


@app.post("/api/calls/{call_id}/swap-speakers")
def swap(call_id: str):
    ingest.swap_speakers(call_id)
    _work.submit(_review_bg, call_id)
    return {"swapped": True}


@app.post("/api/calls/{call_id}/evaluation")
def evaluate(call_id: str, body: EvaluationIn):
    review_id = body.review_id or (service.latest_review(call_id) or {}).get("id")
    if not review_id:
        raise HTTPException(404, "no review to evaluate")
    try:
        result = corrections.submit(call_id, review_id, [i.model_dump() for i in body.items], body.analyst, body.comments)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    new_version = None
    if result["corrections"]:
        try:
            new_version = playbook.build()["version"]
        except MubitError as exc:
            raise HTTPException(502, f"rule induction failed: {exc}") from exc
    return {**result, "playbook_version": new_version or playbook.latest_version(),
            "rules": playbook.rules(playbook.latest_version())}


# ── Wall and queue ───────────────────────────────────────────────────────────
@app.get("/api/wall")
def wall():
    rows = list_calls(limit=1000)
    rows = [r for r in rows if r["split"] != "heldout"]
    scored = [r for r in rows if r["risk_tier"]]
    return {
        "total": len(rows),
        "scored": len(scored),
        "sampled": sum(1 for r in rows if r["audit"]),
        "breaches": sum(1 for r in rows if r["queue_kind"] == "breach"),
        "to_analyst": sum(1 for r in rows if r["queue_kind"] == "analyst"),
        "tiles": [{"call_id": r["id"], "risk_tier": r["risk_tier"], "pass": r["pass"], "queue": r["queue_kind"],
                   "sampled": bool(r["audit"]), "status": r["status"]} for r in rows],
    }


@app.get("/api/queue")
def queue():
    order = "CASE q.kind WHEN 'breach' THEN 0 WHEN 'analyst' THEN 1 WHEN 'audit' THEN 2 ELSE 3 END"
    return db.query(
        "SELECT q.*, c.agent_name, c.split, r.risk_tier, r.score FROM queue q JOIN calls c ON c.id = q.call_id "
        f"LEFT JOIN reviews r ON r.id = q.review_id WHERE q.done = 0 AND q.kind != 'auto' ORDER BY {order}, q.due_at"
    )


# ── Learning ─────────────────────────────────────────────────────────────────
@app.get("/api/learning")
def learning():
    agreement = db.query("SELECT * FROM agreement ORDER BY item_id")
    for a in agreement:
        a["pct"] = round(a["agreed"] / a["n"], 3) if a["n"] else None
    return {
        "playbook_version": playbook.latest_version(),
        "versions": playbook.versions(),
        "corrections": db.query("SELECT * FROM corrections ORDER BY id DESC"),
        "agreement": agreement,
    }


@app.post("/api/corrections/seed")
def seed():
    n = corrections.load_seed()
    version = playbook.build()["version"] if n else playbook.latest_version()
    return {"loaded": n, "playbook_version": version}


@app.post("/api/rules/{correction_id}/test")
def test_rule(correction_id: int, limit: int = 6):
    try:
        return _404(test_on_archive.test_rule, correction_id, limit)
    except MubitError as exc:
        raise HTTPException(502, str(exc)) from exc


# ── Evaluation ───────────────────────────────────────────────────────────────
@app.post("/api/eval")
def start_eval(body: EvalIn):
    latest = playbook.latest_version()
    versions = body.versions if body.versions is not None else sorted({0, latest})
    try:
        runs = [runner.start(body.split, v) for _ in range(body.repeats) for v in versions]
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"run_ids": [r["id"] for r in runs], "versions": versions}


@app.get("/api/runs")
def runs():
    return db.query("SELECT id, label, split, playbook_version, model, status, total, done, error, created_at "
                    "FROM runs ORDER BY created_at DESC")


@app.get("/api/compare")
def compare(split: str = "heldout"):
    return runner.compare(split)


# ── Traces and demo ──────────────────────────────────────────────────────────
@app.get("/api/traces")
def traces(limit: int = 50):
    return db.query("SELECT * FROM traces ORDER BY id DESC LIMIT ?", (max(1, min(limit, 500)),))


@app.post("/api/demo/reset")
def reset(keep_synthetic: bool = True):
    """Clear live calls, evaluations and analyst corrections.

    Keeps synthetic calls and their reviews, the guardrail seed corrections and any playbook
    versions built only from seeds, so the demo restarts from the seeded playbook.
    """
    live = [r["id"] for r in db.query("SELECT id FROM calls WHERE split = 'live'")]
    for cid in live:
        for t in ("utterances", "reviews", "queue", "evaluations"):
            db.execute(f"DELETE FROM {t} WHERE call_id = ?", (cid,))
        db.execute("DELETE FROM calls WHERE id = ?", (cid,))
    seed_ids = {r["id"] for r in db.query("SELECT id FROM corrections WHERE source = 'seed'")}
    for v in db.query("SELECT version, correction_ids FROM playbook_versions"):
        if not set(v["correction_ids"]) <= seed_ids:
            db.execute("DELETE FROM playbook_versions WHERE version = ?", (v["version"],))
    db.execute("DELETE FROM corrections WHERE source != 'seed'")
    db.execute("DELETE FROM reviews WHERE run_id IN ('compare', 'archive')")
    for t in ("agreement", "evaluations"):
        db.execute(f"DELETE FROM {t}")
    if not keep_synthetic:
        for t in ("utterances", "reviews", "queue", "calls", "runs", "traces", "corrections", "playbook_versions"):
            db.execute(f"DELETE FROM {t}")
    return {"cleared_live_calls": len(live), "kept_synthetic": keep_synthetic}
