"""The frozen contract of the review.call task, as pure functions.

What Mubit sees (and must not change once training starts, README §3.4):
- system prompt = app/llm/prompts/review_call.md with data/scorecard.json rendered in;
- output format = app/llm/schemas/call_review.json (strict);
- user message = build_user_message(): playbook rules + redacted transcript.

What stays in plain code: the evidence check, the score, pass/fail and the
risk tier. They're deterministic and auditable.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

from app.config import CRITICAL_CONFIDENCE, SCORECARD_PATH

PROMPTS = Path(__file__).resolve().parents[1] / "llm" / "prompts"
SCHEMAS = Path(__file__).resolve().parents[1] / "llm" / "schemas"
ANSWERS = ("yes", "no", "na", "unsure")
NEVER_NA = {"C3", "S4"}


@lru_cache(maxsize=1)
def scorecard() -> dict:
    return json.loads(SCORECARD_PATH.read_text(encoding="utf-8"))


def items_by_id() -> dict[str, dict]:
    return {i["id"]: i for i in scorecard()["items"]}


@lru_cache(maxsize=1)
def system_prompt() -> str:
    sc = scorecard()
    lines = []
    for it in sc["items"]:
        kind = "CRITICAL (auto-fail)" if it["kind"] == "critical" else f"scored, {it['weight']} points"
        lines.append(f"{it['id']} {it['label']} [{kind}; basis: {it['basis']}]\n   {it['guidance']}")
    template = (PROMPTS / "review_call.md").read_text(encoding="utf-8").strip()
    return template.replace("{bank}", sc["bank"]).replace("{scorecard}", "\n".join(lines))


@lru_cache(maxsize=1)
def schema() -> dict:
    return json.loads((SCHEMAS / "call_review.json").read_text(encoding="utf-8"))


def render_rules(rules: list[dict], version: int) -> str:
    lines = [f"BANK QA PLAYBOOK (v{version})"]
    if not rules:
        lines.append("No rules yet.")
    for i, r in enumerate(rules, 1):
        when = f" (applies when: {r['applies_when']})" if r.get("applies_when") else ""
        lines.append(f"{i}. {r['rule']}{when}")
    return "\n".join(lines)


def build_user_message(utterances: list[dict], rules: list[dict], version: int) -> str:
    """utterances: [{speaker, text, start_s}] with text already redacted."""
    lines = [render_rules(rules, version), "", "TRANSCRIPT"]
    for u in utterances:
        lines.append(f"[{float(u['start_s']):.1f}] {u['speaker'].upper()}: {u['text'].strip()}")
    return "\n".join(lines)


# ── Evidence check ───────────────────────────────────────────────────────────
def _norm(s: str) -> str:
    s = s.lower().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"[^a-z0-9'\[\]£ ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _find(quote: str, utterances: list[dict]) -> dict | None:
    q = _norm(quote)
    if len(q) < 3:
        return None
    for u in utterances:
        if q in _norm(u["text"]):
            return u
    # Tolerate small transcription differences: 80% of the quote's words in one line.
    words = q.split()
    for u in utterances:
        have = set(_norm(u["text"]).split())
        if len(words) >= 4 and sum(w in have for w in words) / len(words) >= 0.8:
            return u
    return None


def verify(output: dict, utterances: list[dict]) -> tuple[dict, list[dict]]:
    """Drop quotes that aren't in the transcript; enforce 'positive evidence to pass' on critical items.

    Returns (items_by_id, issues). Missing items come back as "unsure".
    """
    defs = items_by_id()
    issues: list[dict] = []
    got = {i["id"]: i for i in output.get("items", []) if i.get("id") in defs}
    items: dict[str, dict] = {}
    for item_id, d in defs.items():
        it = got.get(item_id)
        if it is None:
            issues.append({"item": item_id, "issue": "missing from model output"})
            items[item_id] = {"id": item_id, "answer": "unsure", "reasoning": "Not returned by the model.",
                              "evidence": [], "confidence": 0.0, "model_answer": None}
            continue
        kept = []
        for ev in it.get("evidence", []):
            hit = _find(ev.get("quote", ""), utterances)
            if hit is None:
                issues.append({"item": item_id, "issue": "quote not in transcript", "quote": ev.get("quote", "")})
            else:
                kept.append({"quote": ev["quote"], "start_s": float(hit["start_s"]), "speaker": hit["speaker"]})
        answer = it["answer"] if it["answer"] in ANSWERS else "unsure"
        conf = max(0.0, min(1.0, float(it.get("confidence") or 0)))
        if answer == "na" and item_id in NEVER_NA:
            issues.append({"item": item_id, "issue": "na not allowed for this item"})
            answer = "unsure"
        if answer == "yes" and d["kind"] == "critical" and not kept:
            issues.append({"item": item_id, "issue": "critical pass without evidence"})
            answer = "unsure"
        items[item_id] = {"id": item_id, "answer": answer, "reasoning": it.get("reasoning", ""),
                          "evidence": kept, "confidence": conf, "model_answer": it["answer"]}
    return items, issues


# ── Score (plain code) ───────────────────────────────────────────────────────
def score(items: dict[str, dict]) -> dict:
    defs = items_by_id()
    critical = [i for i in defs.values() if i["kind"] == "critical"]
    scored = [i for i in defs.values() if i["kind"] == "scored"]
    critical_fails = [i["id"] for i in critical if items[i["id"]]["answer"] == "no"]
    applicable = [i for i in scored if items[i["id"]]["answer"] != "na"]
    earned = sum(i["weight"] for i in applicable if items[i["id"]]["answer"] == "yes")
    possible = sum(i["weight"] for i in applicable)
    pct = round(100 * earned / possible, 1) if possible else 100.0
    passed = not critical_fails and pct >= scorecard()["pass_mark"]
    confident_breach = any(items[c]["confidence"] >= CRITICAL_CONFIDENCE for c in critical_fails)
    unsure_critical = [i["id"] for i in critical if items[i["id"]]["answer"] == "unsure"]
    if confident_breach:
        tier = "critical"
    elif critical_fails or unsure_critical:
        tier = "high"
    elif not passed:
        tier = "medium"
    else:
        tier = "low"
    return {"score": pct, "pass": passed, "critical_fails": critical_fails, "risk_tier": tier}
