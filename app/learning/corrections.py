"""Capture bid-manager corrections of drafted answers."""
import json
import time

from app import db
from app.config import CORRECTIONS_DIR
from app.models import CorrectionIn

RANK = {"Comply": 3, "Partially Comply": 2, "Do Not Comply": 1, "Not Applicable": 0}


def classify(before: dict | None, after: dict) -> list[str]:
    """Deterministic correction types from the diff between draft and correction."""
    if not before:
        return ["seeded"]
    types = []
    if before.get("status") != after["status"]:
        types.append("status_change")
        if RANK.get(before.get("status"), 0) > RANK.get(after["status"], 0):
            types.append("over_promise_fixed")
    if set(after.get("evidence_ids") or []) - set(before.get("evidence_ids") or []):
        types.append("citation_added")
    if (after.get("gaps") or "").strip() and not (before.get("gaps") or "").strip():
        types.append("gap_added")
    if (before.get("response") or "").strip() != (after.get("response") or "").strip():
        types.append("response_rewritten")
    return types or ["confirmed"]


def submit(c: CorrectionIn) -> dict:
    draft = db.one("SELECT * FROM drafts WHERE run_id = ? AND req_id = ?", (c.run_id, c.req_id))
    if not draft:
        raise KeyError(f"No draft {c.req_id} in run {c.run_id}")
    run = db.one("SELECT package FROM runs WHERE id = ?", (c.run_id,))
    before = {k: draft[k] for k in ("status", "response", "evidence_ids", "gaps", "confidence")}
    after = {"status": c.status, "response": c.response, "evidence_ids": c.evidence_ids, "gaps": c.gaps}
    cid = db.insert("corrections", {
        "ts": time.time(),
        "package": run["package"] if run else None,
        "run_id": c.run_id,
        "req_id": c.req_id,
        "requirement": draft["requirement"],
        "model_output": before,
        "corrected_output": after,
        "correction_type": classify(before, after),
        "rationale": c.rationale.strip(),
        "editor": c.editor,
        "request_id": draft["request_id"],
    })
    return get(cid)


def get(cid: int) -> dict:
    return db.one("SELECT * FROM corrections WHERE id = ?", (cid,))


def all_corrections() -> list[dict]:
    return db.query("SELECT * FROM corrections ORDER BY id")


def delete(cid: int) -> None:
    db.execute("DELETE FROM corrections WHERE id = ?", (cid,))


def load_seed() -> int:
    """Load pre-recorded corrections (data/corrections/seed.jsonl) once."""
    path = CORRECTIONS_DIR / "seed.jsonl"
    existing = {(r["req_id"], r["editor"]) for r in all_corrections()}
    n = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        s = json.loads(line)
        if (s["requirement_id"], s["editor"]) in existing:
            continue
        db.insert("corrections", {
            "ts": time.time(),
            "package": s["package"],
            "run_id": None,
            "req_id": s["requirement_id"],
            "requirement": s["requirement"],
            "model_output": None,
            "corrected_output": s["corrected_output"],
            "correction_type": s.get("correction_type", ["seeded"]),
            "rationale": s["rationale"],
            "editor": s["editor"],
            "request_id": None,
        })
        n += 1
    return n
