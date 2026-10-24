"""Review one call: build the message, call Mubit, check evidence, score, route, store."""
import time

from app import db
from app.config import HELD_OUT_RECORD, MUBIT_MODEL, REVIEW_REASONING_EFFORT
from app.learning import playbook
from app.llm import mubit_client
from app.review import route as routing
from app.review import spec


def utterances(call_id: str) -> list[dict]:
    rows = db.query("SELECT * FROM utterances WHERE call_id = ? ORDER BY idx", (call_id,))
    return [{"speaker": r["speaker"], "text": r["text_redacted"], "raw": r["text_raw"],
             "start_s": r["start_s"], "end_s": r["end_s"], "confidence": r["confidence"]} for r in rows]


def record_mode(call: dict, version: int) -> str:
    """Base reviews and held-out calls never become Mubit training examples."""
    return HELD_OUT_RECORD if version == 0 or call["split"] == "heldout" else "full"


def review_call(call_id: str, version: int | None = None, *, run_id: str | None = None,
                update_queue: bool = True, model: str | None = None) -> dict:
    call = db.one("SELECT * FROM calls WHERE id = ?", (call_id,))
    if not call:
        raise KeyError(call_id)
    version = playbook.latest_version() if version is None else version
    utts = utterances(call_id)
    if not utts:
        raise ValueError(f"call {call_id} has no transcript")
    record = record_mode(call, version)
    model = model or MUBIT_MODEL
    user = spec.build_user_message(utts, playbook.rules(version), version)
    base = {"call_id": call_id, "run_id": run_id, "playbook_version": version, "model": model,
            "record_mode": record, "created_at": time.time()}
    try:
        res = mubit_client.call("review.call", spec.system_prompt(), user, spec.schema(),
                                call_id=call_id, run_id=run_id, record=record, model=model,
                                reasoning_effort=REVIEW_REASONING_EFFORT)
    except mubit_client.MubitError as exc:
        rid = db.insert("reviews", {**base, "request_id": exc.request_id, "error": str(exc)[:500]})
        return db.one("SELECT * FROM reviews WHERE id = ?", (rid,))

    items, issues = spec.verify(res["output"], utts)
    scored = spec.score(items)
    review_id = db.insert("reviews", {
        **base,
        "request_id": res["request_id"], "served_by": res["served_by"], "latency_ms": res["latency_ms"],
        "tokens_in": res["tokens_in"], "tokens_out": res["tokens_out"],
        "output_json": res["output"], "items_json": items, "issues_json": issues,
        "score": scored["score"], "pass": int(scored["pass"]),
        "critical_fails": scored["critical_fails"], "risk_tier": scored["risk_tier"],
    })
    if update_queue:
        q = routing.route(call, utts, items, scored, issues)
        db.upsert("queue", {"call_id": call_id, "review_id": review_id, "kind": q["kind"],
                            "reasons_json": q["reasons"], "audit": int(q["audit"]), "due_at": q["due_at"], "done": 0})
        db.update("calls", {"id": call_id}, {"status": "scored"})
    return db.one("SELECT * FROM reviews WHERE id = ?", (review_id,))


def latest_review(call_id: str) -> dict | None:
    return db.one("SELECT * FROM reviews WHERE call_id = ? AND run_id IS NULL AND error IS NULL ORDER BY id DESC LIMIT 1",
                  (call_id,))
