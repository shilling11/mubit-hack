"""rfp.draft_response: compliance status + response per requirement, via Mubit."""
import re

from app.learning import playbook
from app.llm import mubit_client
from app.models import STATUSES, Requirement
from app.pipeline.retrieve import retrieve

DRAFT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": STATUSES},
        "response": {"type": "string"},
        "evidence_ids": {"type": "array", "items": {"type": "string"}},
        "gaps": {"type": "string"},
        "confidence": {"type": "number"},
    },
    "required": ["status", "response", "evidence_ids", "gaps", "confidence"],
    "additionalProperties": False,
}

FIGURE_RE = re.compile(r"\b\d+(?:\.\d+)?\s?(?:%|per ?cent|minutes?|mins?|hours?|hrs?|days?)", re.I)


def build_user_message(req: Requirement, client: str, evidence: list, playbook_version: int) -> str:
    ev = "\n".join(f"[{e.id}] {e.source} — {e.title}: {e.text}" for e in evidence) or "(no evidence found)"
    return (
        f"CLIENT: {client}\n\n"
        f"REQUIREMENT\nID: {req.id} | Sheet: {req.sheet} | Category: {req.category} | "
        f"Priority: {req.priority or 'n/a'} | Mandatory: {req.mandatory or 'n/a'}\n"
        f"Text: {req.text}\n\n"
        f"EVIDENCE (supplier knowledge base)\n{ev}\n\n"
        f"{playbook.render(playbook_version, f'{req.category} {req.text}')}"
    )


def _norm_figure(s: str) -> str:
    return re.sub(r"\s+", "", s.lower()).replace("percent", "%").replace("per cent", "%")


def detect_flags(out: dict, evidence: list) -> list[str]:
    """Deterministic over-promise signals (no LLM)."""
    flags = []
    retrieved = {e.id for e in evidence}
    cited = out.get("evidence_ids") or []
    if out["status"] in ("Comply", "Partially Comply") and not cited:
        flags.append("no_evidence")
    if any(c not in retrieved for c in cited):
        flags.append("invalid_citation")
    if out["status"] == "Comply":
        # A Comply answer that quotes a figure the evidence doesn't contain is
        # usually echoing the client's ask (e.g. 99.99%) as a commitment.
        ev_figs = {_norm_figure(m) for m in FIGURE_RE.findall(" ".join(e.text for e in evidence))}
        for fig in FIGURE_RE.findall(out.get("response") or ""):
            if _norm_figure(fig) not in ev_figs:
                flags.append(f"unsupported_figure:{fig.strip()}")
    if (out.get("confidence") or 0) < 0.6:
        flags.append("low_confidence")
    if out["status"] == "Comply" and any(f != "low_confidence" for f in flags):
        flags.append("over_promise_risk")
    return flags


def draft_one(
    req: Requirement,
    client: str,
    playbook_version: int,
    *,
    run_id: str | None = None,
    record: str = "full",
    model: str | None = None,
) -> dict:
    evidence = retrieve(f"{req.category} {req.text}")
    user = build_user_message(req, client, evidence, playbook_version)
    res = mubit_client.call(
        "rfp.draft_response", user, DRAFT_SCHEMA,
        run_id=run_id, record=record, model=model,
    )
    out = res["output"]
    out["evidence_ids"] = [e for e in out.get("evidence_ids", []) if isinstance(e, str)]
    out["confidence"] = max(0.0, min(1.0, float(out.get("confidence") or 0)))
    return {
        **out,
        "flags": detect_flags(out, evidence),
        "retrieved": [e.model_dump() for e in evidence],
        "request_id": res["request_id"],
        "served_by": res["served_by"],
        "latency_ms": res["latency_ms"],
        "tokens_in": res["tokens_in"],
        "tokens_out": res["tokens_out"],
    }
