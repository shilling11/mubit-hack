"""Conservative routing (plain code, README §4.5)."""
import hashlib
import time

from app.config import AUDIT_RATE, CRITICAL_CONFIDENCE, SCORED_CONFIDENCE, STT_MIN_CONFIDENCE
from app.review import safety_net
from app.review.spec import items_by_id

DUE_S = {"breach": 4 * 3600, "analyst": 24 * 3600, "audit": 5 * 24 * 3600}


def in_audit_sample(call_id: str) -> bool:
    """A stable random 5% sample, independent of the model (keeps accuracy figures honest)."""
    h = int(hashlib.sha256(call_id.encode()).hexdigest()[:8], 16)
    return h / 0xFFFFFFFF < AUDIT_RATE


def route(call: dict, utterances: list[dict], items: dict[str, dict], scored: dict, issues: list[dict]) -> dict:
    defs = items_by_id()
    reasons: list[str] = []
    breach = False
    for item_id in scored["critical_fails"]:
        if items[item_id]["confidence"] >= CRITICAL_CONFIDENCE:
            breach = True
            reasons.append(f"breach: {item_id} {defs[item_id]['label']} failed (confidence {items[item_id]['confidence']:.2f})")
        else:
            reasons.append(f"possible breach: {item_id} failed with low confidence ({items[item_id]['confidence']:.2f})")
    for item_id, it in items.items():
        d = defs[item_id]
        if it["answer"] == "unsure":
            reasons.append(f"{item_id} unsure" + (" (critical)" if d["kind"] == "critical" else ""))
        elif d["kind"] == "critical" and it["answer"] != "no" and it["confidence"] < CRITICAL_CONFIDENCE:
            reasons.append(f"{item_id} low confidence ({it['confidence']:.2f})")
        elif d["kind"] == "scored" and it["confidence"] < SCORED_CONFIDENCE:
            reasons.append(f"{item_id} low confidence ({it['confidence']:.2f})")
    reasons += safety_net.check(utterances, items)
    if any(i["issue"] == "quote not in transcript" for i in issues):
        reasons.append("model quoted text that isn't in the transcript")
    stt = call.get("stt_confidence")
    if stt is not None and stt < STT_MIN_CONFIDENCE:
        reasons.append(f"low transcription confidence ({stt:.2f})")

    audit = in_audit_sample(call["id"])
    if breach:
        kind = "breach"
    elif reasons:
        kind = "analyst"
    elif audit:
        kind = "audit"
    else:
        kind = "auto"
    if audit:
        reasons.append("random audit sample")
    due = DUE_S.get(kind)
    return {"kind": kind, "reasons": reasons, "audit": audit, "due_at": time.time() + due if due else None}
