"""Background execution of a drafting run over one RFP package."""
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from app import db
from app.config import MAX_PARALLEL, MUBIT_MODEL
from app.eval.score import score_run
from app.ingest import packages
from app.learning import playbook
from app.models import RunIn
from app.pipeline.draft import draft_one

# Baseline (playbook v0) answers are the ones bid managers correct, so we keep
# them out of Mubit's training examples by default.
BASELINE_RECORD = os.getenv("REDLINE_BASELINE_RECORD", "metadata")

_runs = ThreadPoolExecutor(max_workers=2, thread_name_prefix="run")
_calls = ThreadPoolExecutor(max_workers=MAX_PARALLEL, thread_name_prefix="call")


def start(spec: RunIn) -> dict:
    info = packages.package_info(spec.package)
    reqs = packages.requirements(spec.package)
    if spec.sheets:
        reqs = [r for r in reqs if r.sheet in spec.sheets]
    if spec.req_ids:
        reqs = [r for r in reqs if r.id in spec.req_ids]
    if not reqs:
        raise ValueError("No requirements selected")
    version = playbook.latest_version() if spec.playbook_version is None else spec.playbook_version
    playbook.get_version(version)  # validate
    run_id = f"run_{uuid.uuid4().hex[:10]}"
    model = spec.model or MUBIT_MODEL
    label = spec.label or ("Base (no playbook)" if version == 0 else f"Playbook v{version}")
    if model != MUBIT_MODEL:
        label += f" · {model}"
    db.insert("runs", {
        "id": run_id, "package": spec.package, "playbook_version": version, "model": model,
        "label": label, "status": "running", "created": time.time(), "total": len(reqs), "done": 0,
    })
    for r in reqs:
        db.upsert("drafts", {
            "run_id": run_id, "req_id": r.id, "sheet": r.sheet, "category": r.category,
            "requirement": r.text, "mandatory": r.mandatory, "priority": r.priority,
        })
    record = BASELINE_RECORD if version == 0 else "full"
    _runs.submit(_execute, run_id, info, reqs, version, model, record)
    return get(run_id)


def _execute(run_id, info, reqs, version, model, record) -> None:
    client = info.get("client") or info["slug"]

    def one(req):
        try:
            d = draft_one(req, client, version, run_id=run_id, record=record, model=model)
            db.update("drafts", {"run_id": run_id, "req_id": req.id}, {
                k: d[k] for k in ("status", "response", "evidence_ids", "gaps", "confidence", "flags", "retrieved",
                                  "request_id", "served_by", "latency_ms", "tokens_in", "tokens_out")
            })
        except Exception as exc:
            db.update("drafts", {"run_id": run_id, "req_id": req.id}, {"error": str(exc)[:500]})
        db.execute("UPDATE runs SET done = done + 1 WHERE id = ?", (run_id,))

    try:
        list(_calls.map(one, reqs))
        finish(run_id)
    except Exception as exc:
        db.update("runs", {"id": run_id}, {"status": "failed", "error": str(exc)[:500], "finished": time.time()})


def finish(run_id: str) -> None:
    run = db.one("SELECT * FROM runs WHERE id = ?", (run_id,))
    drafts = get_drafts(run_id)
    gold = packages.gold(run["package"])
    score = score_run(drafts, gold) if gold else None
    errors = sum(1 for d in drafts if d.get("error"))
    db.update("runs", {"id": run_id}, {
        "status": "done" if errors < len(drafts) else "failed",
        "finished": time.time(),
        "score_json": score,
        "error": f"{errors} requirement(s) failed" if errors else None,
    })


def get(run_id: str) -> dict:
    run = db.one("SELECT * FROM runs WHERE id = ?", (run_id,))
    if not run:
        raise KeyError(run_id)
    return run


def get_drafts(run_id: str) -> list[dict]:
    return db.query("SELECT * FROM drafts WHERE run_id = ? ORDER BY rowid", (run_id,))


def list_runs(package: str | None = None) -> list[dict]:
    if package:
        return db.query("SELECT * FROM runs WHERE package = ? ORDER BY created DESC", (package,))
    return db.query("SELECT * FROM runs ORDER BY created DESC")
