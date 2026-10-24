"""Analyst evaluations of an AI scorecard → corrections and agreement (README §4.6)."""
import json
import time

from app import db
from app.config import CORRECTIONS_DIR
from app.review.spec import items_by_id


def _excerpt(call_id: str, item: dict, utts: list[dict], around: int = 2) -> str:
    """Transcript lines near the item's evidence (redacted), for rule induction."""
    starts = [e["start_s"] for e in item.get("evidence", [])]
    if not starts:
        chosen = utts[:8]
    else:
        idx = {i for i, u in enumerate(utts) for s in starts if abs(u["start_s"] - s) < 0.01}
        keep = {j for i in idx for j in range(max(0, i - around), min(len(utts), i + around + 1))}
        chosen = [utts[i] for i in sorted(keep)] or utts[:8]
    return "\n".join(f"[{u['start_s']:.1f}] {u['speaker'].upper()}: {u['text']}" for u in chosen)


def submit(call_id: str, review_id: int, answers: list[dict], analyst: str = "analyst", comments: str = "") -> dict:
    """answers: [{id, answer, reason}] for any items the analyst touched; untouched items count as agreed."""
    from app.review.service import utterances

    review = db.one("SELECT * FROM reviews WHERE id = ? AND call_id = ?", (review_id, call_id))
    if not review or not review.get("items_json"):
        raise KeyError(f"review {review_id} for call {call_id}")
    items = review["items_json"]
    by_id = {a["id"]: a for a in answers if a.get("id") in items}
    for item_id, a in by_id.items():
        if a.get("answer") and a["answer"] != items[item_id]["answer"] and not (a.get("reason") or "").strip():
            raise ValueError(f"{item_id}: a reason is required when changing the AI's answer")
    utts = utterances(call_id)
    final, corrections = [], []
    for item_id in items_by_id():
        ai = items[item_id]["answer"]
        a = by_id.get(item_id)
        after = a["answer"] if a and a.get("answer") else ai
        agreed = after == ai
        final.append({"id": item_id, "ai": ai, "answer": after, "agreed": agreed, "reason": (a or {}).get("reason", "")})
        row = db.one("SELECT * FROM agreement WHERE item_id = ?", (item_id,)) or {"n": 0, "agreed": 0}
        db.upsert("agreement", {"item_id": item_id, "n": row["n"] + 1, "agreed": row["agreed"] + int(agreed),
                                "updated_at": time.time()})
        if not agreed:
            cid = db.insert("corrections", {
                "call_id": call_id, "review_id": review_id, "item_id": item_id, "before": ai, "after": after,
                "reason": a["reason"].strip(), "excerpt": _excerpt(call_id, items[item_id], utts),
                "source": "analyst", "created_at": time.time(),
            })
            corrections.append(db.one("SELECT * FROM corrections WHERE id = ?", (cid,)))
    eid = db.insert("evaluations", {"call_id": call_id, "review_id": review_id, "analyst": analyst,
                                    "items_json": final, "comments": comments, "submitted_at": time.time()})
    db.update("queue", {"call_id": call_id}, {"done": 1})
    return {"evaluation_id": eid, "items": final, "corrections": corrections}


def load_seed() -> int:
    """Guardrail corrections (data/corrections/seed.jsonl), loaded once."""
    path = CORRECTIONS_DIR / "seed.jsonl"
    if not path.exists():
        return 0
    have = {(c["item_id"], c["reason"]) for c in db.query("SELECT item_id, reason FROM corrections")}
    n = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        s = json.loads(line)
        if (s["item_id"], s["reason"]) in have:
            continue
        db.insert("corrections", {"call_id": None, "review_id": None, "item_id": s["item_id"], "before": s.get("before"),
                                  "after": s["after"], "reason": s["reason"], "excerpt": s.get("excerpt", ""),
                                  "source": "seed", "created_at": time.time()})
        n += 1
    return n
