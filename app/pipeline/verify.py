"""rfp.verify_claims: check a draft's claims against its evidence, via Mubit."""
from app.llm import mubit_client
from app.models import STATUSES
from app.pipeline.retrieve import by_id

VERIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "supported": {"type": "boolean"},
                    "evidence_id": {"type": "string"},
                },
                "required": ["claim", "supported", "evidence_id"],
                "additionalProperties": False,
            },
        },
        "over_promise": {"type": "boolean"},
        "suggested_status": {"type": "string", "enum": STATUSES},
        "reason": {"type": "string"},
    },
    "required": ["claims", "over_promise", "suggested_status", "reason"],
    "additionalProperties": False,
}


def verify_draft(draft: dict, run_id: str | None = None) -> dict:
    kb = by_id()
    ids = list(dict.fromkeys((draft.get("evidence_ids") or []) + [e["id"] for e in draft.get("retrieved") or []]))
    ev = "\n".join(f"[{i}] {kb[i].title}: {kb[i].text}" for i in ids if i in kb) or "(no evidence)"
    user = (
        f"REQUIREMENT ({draft['req_id']}): {draft['requirement']}\n\n"
        f"DRAFT STATUS: {draft['status']}\nDRAFT RESPONSE: {draft['response']}\nDRAFT GAPS: {draft.get('gaps') or ''}\n\n"
        f"EVIDENCE\n{ev}"
    )
    res = mubit_client.call("rfp.verify_claims", user, VERIFY_SCHEMA, run_id=run_id)
    return {**res["output"], "request_id": res["request_id"]}
