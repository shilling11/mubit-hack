"""The bid playbook: versioned rules induced from corrections.

Version 0 is the empty playbook. Building a new version induces a generalised
rule from each new correction (via Mubit, task rfp.induce_rule) and snapshots
the full rule set. Draft calls include the playbook in the *user* message, so
the Mubit task (fixed system prompt) stays the same and every corrected call is
a kept example Mubit can train the task adapter on.
"""
import time

from app import db
from app.learning.corrections import all_corrections
from app.llm import mubit_client
from app.pipeline.retrieve import rank_texts

MAX_EXAMPLES = 2

RULE_SCHEMA = {
    "type": "object",
    "properties": {
        "rule": {"type": "string"},
        "applies_when": {"type": "string"},
        "keywords": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["rule", "applies_when", "keywords"],
    "additionalProperties": False,
}


def latest_version() -> int:
    row = db.one("SELECT MAX(version) AS v FROM playbook_versions")
    return (row or {}).get("v") or 0


def get_version(version: int) -> dict:
    if version == 0:
        return {"version": 0, "created": None, "correction_ids": [], "rules": [], "note": "Empty playbook (base)"}
    row = db.one("SELECT * FROM playbook_versions WHERE version = ?", (version,))
    if not row:
        raise KeyError(f"Playbook v{version} not found")
    return row


def versions() -> list[dict]:
    return [get_version(0)] + db.query("SELECT * FROM playbook_versions ORDER BY version")


def _induce(c: dict) -> dict:
    after = c["corrected_output"]
    before = c["model_output"] or {}
    user = (
        f"REQUIREMENT ({c['req_id']}): {c['requirement']}\n\n"
        f"AI DRAFT: status={before.get('status', 'n/a')}; response={before.get('response', 'n/a')}\n\n"
        f"CORRECTED: status={after['status']}; response={after['response']}; gaps={after.get('gaps', '')}\n\n"
        f"BID MANAGER RATIONALE: {c['rationale']}"
    )
    out = mubit_client.call("rfp.induce_rule", user, RULE_SCHEMA)["output"]
    db.update("corrections", {"id": c["id"]}, {"rule": out})
    return out


def build(note: str | None = None) -> dict:
    """Create playbook v(N+1) from all corrections so far."""
    corrections = all_corrections()
    if not corrections:
        raise ValueError("No corrections yet: teach Redline at least one correction first.")
    rules = []
    for c in corrections:
        rule = c["rule"] if isinstance(c.get("rule"), dict) else None
        rule = rule or _induce(c)
        rules.append({
            "correction_id": c["id"],
            "req_id": c["req_id"],
            "package": c["package"],
            "requirement": c["requirement"],
            "status": c["corrected_output"]["status"],
            "rationale": c["rationale"],
            "rule": rule["rule"],
            "applies_when": rule["applies_when"],
            "keywords": rule["keywords"],
        })
    version = latest_version() + 1
    db.insert("playbook_versions", {
        "version": version,
        "created": time.time(),
        "correction_ids": [c["id"] for c in corrections],
        "rules": rules,
        "note": note or f"{len(rules)} rules from {len(corrections)} corrections",
    })
    return get_version(version)


def render(version: int, requirement_text: str) -> str:
    """Playbook block for a draft call's user message."""
    pb = get_version(version)
    rules = pb["rules"]
    if not rules:
        return "BID TEAM PLAYBOOK\nNo playbook rules yet."
    scores = rank_texts(
        requirement_text,
        [f"{r['requirement']} {r['applies_when']} {' '.join(r['keywords'])}" for r in rules],
    )
    order = sorted(range(len(rules)), key=lambda i: -scores[i])
    lines = [f"BID TEAM PLAYBOOK (v{version})", "Rules:"]
    for n, i in enumerate(order, start=1):
        r = rules[i]
        lines.append(f"{n}. {r['rule']} (Applies when: {r['applies_when']})")
    examples = [rules[i] for i in order[:MAX_EXAMPLES] if scores[i] > 0]
    if examples:
        lines.append("Worked examples from past corrections:")
        for r in examples:
            lines.append(f"- Requirement: \"{r['requirement']}\" -> {r['status']}. Bid manager: {r['rationale']}")
    return "\n".join(lines)
