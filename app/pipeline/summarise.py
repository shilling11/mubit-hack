"""rfp.exec_summary: executive summary and win-risk analysis, via Mubit."""
from collections import Counter

from app.llm import mubit_client

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "win_risks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "requirement_id": {"type": "string"},
                    "risk": {"type": "string"},
                    "action": {"type": "string"},
                },
                "required": ["requirement_id", "risk", "action"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["summary", "win_risks"],
    "additionalProperties": False,
}


def summarise(run: dict, drafts: list[dict], package: dict) -> dict:
    counts = Counter(d["status"] for d in drafts if d.get("status"))
    gaps = "\n".join(
        f"- {d['req_id']} ({d['status']}): {d['requirement']} | gap: {d.get('gaps') or 'n/a'}"
        for d in drafts if d.get("status") in ("Partially Comply", "Do Not Comply")
    ) or "(none)"
    user = (
        f"CLIENT: {package.get('client')}\nOPPORTUNITY: {package.get('opportunity')} ({package.get('reference')})\n\n"
        f"COMPLIANCE POSITION: " + ", ".join(f"{k}: {v}" for k, v in counts.items()) + "\n\n"
        f"GAPS AND NON-COMPLIANCES\n{gaps}"
    )
    res = mubit_client.call("rfp.exec_summary", user, SUMMARY_SCHEMA, run_id=run["id"])
    return {**res["output"], "request_id": res["request_id"]}
