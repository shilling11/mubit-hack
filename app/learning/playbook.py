"""The QA playbook: versioned rules induced from analysts' corrections (README §4.7).

v0 is empty. Building v(N+1) asks Mubit (rule.induce) to turn each new
correction into a general rule and snapshots the full rule set. Reviews carry
the playbook in the *user* message, so review.call stays one Mubit task and
every review made with the playbook is a training example of the corrected
behaviour.
"""
import time
from functools import lru_cache
from pathlib import Path

from app import db
from app.llm import mubit_client
from app.review.spec import items_by_id

PROMPT = Path(__file__).resolve().parents[1] / "llm" / "prompts" / "rule_induce.md"

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


@lru_cache(maxsize=1)
def _system() -> str:
    return PROMPT.read_text(encoding="utf-8").strip()


def latest_version() -> int:
    row = db.one("SELECT MAX(version) AS v FROM playbook_versions")
    return (row or {}).get("v") or 0


def get_version(version: int) -> dict:
    if version == 0:
        return {"version": 0, "created_at": None, "correction_ids": [], "rules_json": [], "note": "Base: no rules"}
    row = db.one("SELECT * FROM playbook_versions WHERE version = ?", (version,))
    if not row:
        raise KeyError(f"playbook v{version}")
    return row


def rules(version: int) -> list[dict]:
    return get_version(version)["rules_json"]


def versions() -> list[dict]:
    return [get_version(0)] + db.query("SELECT * FROM playbook_versions ORDER BY version")


def pending_corrections() -> list[dict]:
    included = set(get_version(latest_version())["correction_ids"])
    return [c for c in db.query("SELECT * FROM corrections ORDER BY id") if c["id"] not in included]


def _induce(c: dict) -> dict:
    item = items_by_id()[c["item_id"]]
    user = (
        f"SCORECARD ITEM: {item['id']} {item['label']} ({item['kind']})\n"
        f"ITEM GUIDANCE: {item['guidance']}\n\n"
        f"AI ANSWER: {c['before'] or 'n/a'}\n"
        f"ANALYST'S CORRECTED ANSWER: {c['after']}\n"
        f"ANALYST'S REASON: {c['reason']}\n\n"
        f"TRANSCRIPT EXCERPT:\n{c.get('excerpt') or '(none)'}"
    )
    out = mubit_client.call("rule.induce", _system(), user, RULE_SCHEMA, call_id=c.get("call_id"))["output"]
    db.update("corrections", {"id": c["id"]}, {"rule_json": out})
    return out


def build(note: str | None = None) -> dict:
    """Create playbook v(N+1) from every correction so far."""
    corrections = db.query("SELECT * FROM corrections ORDER BY id")
    if not corrections:
        raise ValueError("No corrections yet.")
    out_rules = []
    for c in corrections:
        r = c["rule_json"] if isinstance(c.get("rule_json"), dict) else _induce(c)
        out_rules.append({
            "correction_id": c["id"], "item_id": c["item_id"], "source": c["source"],
            "rule": r["rule"], "applies_when": r["applies_when"], "keywords": r["keywords"],
        })
    version = latest_version() + 1
    db.insert("playbook_versions", {
        "version": version, "created_at": time.time(),
        "correction_ids": [c["id"] for c in corrections], "rules_json": out_rules,
        "note": note or f"{len(out_rules)} rules from {len(corrections)} corrections",
    })
    return get_version(version)
