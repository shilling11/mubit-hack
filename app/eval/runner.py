"""Batch review runs: held-out evaluations (base vs playbook, repeated) and archive re-scoring."""
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from statistics import mean

from app import db
from app.config import MAX_PARALLEL, MUBIT_MODEL
from app.eval.score import load_gold, score_runs
from app.learning import playbook
from app.review import route as routing
from app.review import service, spec

_pool = ThreadPoolExecutor(max_workers=MAX_PARALLEL, thread_name_prefix="review")
_runs = ThreadPoolExecutor(max_workers=2, thread_name_prefix="run")


def _route_kind(call_id: str, review: dict) -> str:
    if not review.get("items_json"):
        return "error"
    call = db.one("SELECT * FROM calls WHERE id = ?", (call_id,))
    items = review["items_json"]
    q = routing.route(call, service.utterances(call_id), items, spec.score(items), review.get("issues_json") or [])
    return q["kind"]


def start(split: str = "heldout", version: int | None = None, label: str | None = None,
          model: str | None = None, call_ids: list[str] | None = None) -> dict:
    version = playbook.latest_version() if version is None else version
    ids = call_ids or [r["id"] for r in db.query("SELECT id FROM calls WHERE split = ? ORDER BY id", (split,))]
    if not ids:
        raise ValueError(f"no calls in split {split!r}")
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    db.insert("runs", {"id": run_id, "label": label or ("Base" if version == 0 else f"Playbook v{version}"),
                       "split": split, "playbook_version": version, "model": model or MUBIT_MODEL,
                       "status": "running", "total": len(ids), "done": 0, "created_at": time.time()})
    _runs.submit(_execute, run_id, ids, version, model)
    return db.one("SELECT * FROM runs WHERE id = ?", (run_id,))


def _execute(run_id: str, ids: list[str], version: int, model: str | None) -> None:
    def one(cid):
        try:
            return service.review_call(cid, version, run_id=run_id, update_queue=False, model=model)
        finally:
            db.execute("UPDATE runs SET done = done + 1 WHERE id = ?", (run_id,))
    try:
        reviews = [r for r in _pool.map(one, ids) if r]
        routes = {r["call_id"]: _route_kind(r["call_id"], r) for r in reviews}
        metrics = score_runs(reviews, routes, load_gold())
        errors = sum(1 for r in reviews if r.get("error"))
        db.update("runs", {"id": run_id}, {"status": "done", "metrics_json": metrics, "finished_at": time.time(),
                                           "error": f"{errors} review(s) failed" if errors else None})
    except Exception as exc:
        db.update("runs", {"id": run_id}, {"status": "failed", "error": str(exc)[:500], "finished_at": time.time()})


def compare(split: str = "heldout") -> list[dict]:
    """Mean and min-max of each metric, per (playbook version, model), over finished full runs."""
    total = (db.one("SELECT COUNT(*) AS n FROM calls WHERE split = ?", (split,)) or {}).get("n", 0)
    runs = db.query("SELECT * FROM runs WHERE split = ? AND status = 'done' AND total = ? ORDER BY created_at", (split, total))
    groups: dict[tuple, list[dict]] = {}
    for r in runs:
        groups.setdefault((r["playbook_version"], r["model"]), []).append(r)
    keys = ["item_accuracy", "system_critical_recall", "model_critical_recall", "false_negatives",
            "critical_precision", "human_queue_rate", "complaint_recall", "vulnerability_recall", "latency_p50_ms", "tokens"]
    out = []
    for (version, model), rs in sorted(groups.items()):
        summary = {}
        for k in keys:
            vals = [r["metrics_json"].get(k) for r in rs if r["metrics_json"].get(k) is not None]
            summary[k] = {"mean": round(mean(vals), 3), "min": min(vals), "max": max(vals)} if vals else None
        latest = rs[-1]["metrics_json"].get("per_call", [])
        out.append({"playbook_version": version, "model": model, "runs": len(rs),
                    "label": "Base" if version == 0 else f"Playbook v{version}",
                    "run_ids": [r["id"] for r in rs], "metrics": summary,
                    "n_items": len(spec.items_by_id()),
                    # Latest run, one entry per held-out call: how many of the 9 items matched gold
                    "per_call": [{"call_id": p["call_id"], "items_correct": p["items_correct"],
                                  "false_negatives": p["false_negatives"]} for p in latest]})
    return out
