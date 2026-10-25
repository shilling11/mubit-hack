"""Redress API. Run with: uvicorn app.main:app --port 8000   (no --reload when demoing)"""
import os
import re
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app import db, demo
from app.capture import importers, ingest, stt, tidy
from app.config import MAX_PARALLEL, MUBIT_API_KEY, MUBIT_BASE_URL, MUBIT_MODEL, DEEPGRAM_API_KEY, REVIEW_REASONING_EFFORT
from app.eval import runner
from app.learning import corrections, playbook, test_on_archive
from app.llm.mubit_client import MubitError
from app.review import service
from app.review.spec import items_by_id, scorecard

_work = ThreadPoolExecutor(max_workers=2, thread_name_prefix="call")
# A monthly batch is scored several calls at a time, apart from live calls
_batch = ThreadPoolExecutor(max_workers=MAX_PARALLEL, thread_name_prefix="batch")


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


def _process_upload(call_id: str, mimetype: str, two_channel: bool = False) -> None:
    try:
        ingest.transcribe_call(call_id, mimetype, two_channel=two_channel)
        review = service.review_call(call_id)
        if review.get("error"):  # the transcript is stored; say why there's no scorecard instead of waiting forever
            db.update("calls", {"id": call_id}, {"status": "failed", "error": f"Transcribed, but not scored: {review['error']}"[:500]})
    except (stt.STTError, MubitError, ValueError) as exc:
        db.update("calls", {"id": call_id}, {"status": "failed", "error": str(exc)[:500]})


def _join_current_batch(call_id: str) -> None:
    """A call taken live joins this month's batch (the latest import), so it's checked alongside the rest."""
    latest = db.one("SELECT id FROM batches ORDER BY created_at DESC LIMIT 1")
    if latest:
        db.update("calls", {"id": call_id}, {"batch_id": latest["id"]})


def _review_bg(call_id: str, version: int | None = None) -> None:
    try:
        review = service.review_call(call_id, version)
        if review.get("error"):  # say why, instead of leaving the call "reviewing" forever
            db.update("calls", {"id": call_id}, {"status": "failed", "error": f"Not scored: {review['error']}"[:500]})
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
async def upload_call(audio: UploadFile = File(...), agent_name: str = Form(""), customer_name: str = Form(""),
                      two_channel: bool = Form(False)):
    """two_channel: a stereo recording with the customer on the left and the colleague on the right."""
    data = await audio.read()
    if not data:
        raise HTTPException(400, "empty recording")
    mimetype = audio.content_type or "audio/webm"
    call_id = ingest.save_recording(data, mimetype, agent_name, customer_name)
    _join_current_batch(call_id)
    _work.submit(_process_upload, call_id, mimetype, two_channel)
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
        _join_current_batch(cid)
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


# ── Monthly batches (the client's export: Excel/CSV, Amazon Connect JSON or pasted text) ─────
_KIND_ORDER = {"breach": 0, "analyst": 1, "audit": 2, "auto": 3}


def _check_order(r: dict) -> tuple:
    """Calls taken live come first (newest first), then the riskiest and lowest-scoring imports."""
    if r["source"] in ("live", "demo"):
        return (0, -r["created_at"], 0)
    return (1, _KIND_ORDER.get(r["queue_kind"], 4), r["score"] if r["score"] is not None else 100)


@app.post("/api/batches")
async def import_batch(files: list[UploadFile] = File(default=[]), text: str = Form(""), name: str = Form(""),
                       review: bool = Form(True)):
    """Import this month's calls and score them all. Files that can't be read are skipped with the reason."""
    calls, agents, skipped, formats = [], {}, [], {}
    for f in files:
        try:
            fmt, out = importers.parse(f.filename or "upload", await f.read())
        except importers.ImportFailed as exc:
            skipped.append({"file": f.filename, "reason": str(exc)})
            continue
        if fmt == "call list":
            agents.update(out)
            formats[fmt] = formats.get(fmt, 0) + 1
        else:
            calls += out
            formats[fmt] = formats.get(fmt, 0) + len(out)
    if text.strip():
        try:
            calls.append(importers.text_transcript(text, f"pasted-{uuid.uuid4().hex[:6]}"))
            formats["pasted text"] = formats.get("pasted text", 0) + 1
        except importers.ImportFailed as exc:
            skipped.append({"file": "pasted text", "reason": str(exc)})
    if not calls:
        detail = "; ".join(f"{s['file']}: {s['reason']}" for s in skipped) or "no files"
        raise HTTPException(400, f"Nothing to import ({detail})")
    batch_id = f"batch_{uuid.uuid4().hex[:6]}"
    db.insert("batches", {"id": batch_id, "name": name or f"{scorecard()['bank']} · {time.strftime('%B %Y')}",
                          "formats": formats, "created_at": time.time()})
    ids = []
    for c in calls:
        utts = [{**u, "text": tidy.dates(u["text"])} for u in c["utterances"] if u["text"].strip()]
        if not utts:
            skipped.append({"file": c["id"], "reason": "no lines"})
            continue
        cid = ingest.create_call(utts, source="import", split="practice", call_id=c["id"],
                                 agent_name=c["agent_name"] or agents.get(c["id"], ""))
        db.update("calls", {"id": cid}, {"batch_id": batch_id, "status": "reviewing" if review else "new"})
        ids.append(cid)
    if review:
        for cid in ids:
            _batch.submit(_review_bg, cid)
    return {"batch_id": batch_id, "count": len(ids), "formats": formats, "skipped": skipped}


def _batch_calls(batch_id: str) -> list[dict]:
    return db.query(
        "SELECT c.id, c.source, c.created_at, c.agent_name, c.status, c.error, q.kind AS queue_kind, q.audit, q.done, r.score, r.pass, "
        "r.risk_tier, r.playbook_version, r.critical_fails, "
        "(SELECT COUNT(*) FROM evaluations e WHERE e.call_id = c.id) AS checked "
        "FROM calls c LEFT JOIN queue q ON q.call_id = c.id LEFT JOIN reviews r ON r.id = q.review_id "
        "WHERE c.batch_id = ? ORDER BY c.id", (batch_id,))


@app.get("/api/batches")
def list_batches():
    return db.query("SELECT b.*, (SELECT COUNT(*) FROM calls c WHERE c.batch_id = b.id) AS total "
                    "FROM batches b ORDER BY b.created_at DESC")


@app.get("/api/batches/{batch_id}")
def get_batch(batch_id: str):
    batch = db.one("SELECT * FROM batches WHERE id = ?", (batch_id,))
    if not batch:
        raise HTTPException(404, batch_id)
    rows, latest = _batch_calls(batch_id), playbook.latest_version()
    open_flags = [r for r in rows if r["queue_kind"] in ("breach", "analyst", "audit") and not r["done"] and not r["checked"]]
    # Calls to check together first: the one just taken live, then the riskiest
    suggested = sorted((r for r in rows if r["status"] == "scored" and not r["checked"]), key=_check_order)
    return {
        **batch, "playbook_version": latest, "rules": len(playbook.rules(latest)),
        "stats": {
            "total": len(rows),
            "scored": sum(r["status"] == "scored" for r in rows),
            "failed": sum(r["status"] == "failed" for r in rows),
            "checked": sum(bool(r["checked"]) for r in rows),
            "current": sum(r["status"] == "scored" and r["playbook_version"] == latest for r in rows),
            "flagged": {k: sum(r["queue_kind"] == k for r in open_flags) for k in ("breach", "analyst", "audit")},
            "auto": sum(r["queue_kind"] == "auto" and not r["checked"] for r in rows),
        },
        "suggested": suggested[:5],
        "calls": rows,
    }


def _words(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower().replace("’", "'")))


def _like_newest_correction(version: int) -> dict[str, int]:
    """{call id: matches} for calls that look like the newest correction: the rule's keywords plus three-word
    phrases from the quote the analyst corrected (the model's keywords don't always use the calls' words)."""
    newest = max(playbook.rules(version), key=lambda r: r.get("correction_id") or 0, default=None)
    if not newest:
        return {}
    phrases = {_words(k) for k in newest.get("keywords", []) if k.strip()}
    fixed = db.one("SELECT c.item_id, r.items_json FROM corrections c JOIN reviews r ON r.id = c.review_id "
                   "WHERE c.id = ?", (newest.get("correction_id"),))
    for ev in ((fixed or {}).get("items_json") or {}).get((fixed or {}).get("item_id"), {}).get("evidence", []):
        w = _words(ev.get("quote", "")).split()
        phrases |= {" ".join(w[i:i + 3]) for i in range(len(w) - 2)}
    hits: dict[str, int] = {}
    for u in db.query("SELECT call_id, text_redacted FROM utterances"):
        text = _words(u["text_redacted"])
        n = sum(p in text for p in phrases if p)
        if n:
            hits[u["call_id"]] = hits.get(u["call_id"], 0) + n
    return hits


@app.post("/api/batches/{batch_id}/finish")
def finish_batch(batch_id: str):
    """Score every call nobody has checked yet with the latest playbook (what the analyst's corrections taught it)."""
    if not db.one("SELECT id FROM batches WHERE id = ?", (batch_id,)):
        raise HTTPException(404, batch_id)
    latest = playbook.latest_version()
    todo = [r["id"] for r in _batch_calls(batch_id) if not r["checked"]
            and (r["status"] == "failed" or r["playbook_version"] != latest)]  # != so a demo reset can go back to v0
    # Re-mark the calls the newest rule is about first, so its effect shows within seconds
    hits = _like_newest_correction(latest)
    todo.sort(key=lambda cid: -hits.get(cid, 0))
    for cid in todo:
        db.update("calls", {"id": cid}, {"status": "reviewing", "error": None})
        _batch.submit(_review_bg, cid)
    return {"queued": len(todo), "playbook_version": latest}


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
    db.execute("UPDATE queue SET done = 0")  # with the checks gone, every call is open again
    if not keep_synthetic:
        for t in ("utterances", "reviews", "queue", "calls", "runs", "traces", "corrections", "playbook_versions"):
            db.execute(f"DELETE FROM {t}")
    return {"cleared_live_calls": len(live), "kept_synthetic": keep_synthetic}
