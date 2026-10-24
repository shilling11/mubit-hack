"""The frozen contract for the call review task (review.<client>), as pure functions.

What Mubit sees:
- System prompt: app/llm/prompts/review_<client>.md. FROZEN at 00:00 Sun.
  The client's scorecard lives here, so each bank client is its own Mubit task
  and gets its own adapter (README §3.4).
- Output format: app/llm/schemas/call_review.json (strict). FROZEN at 00:00.
- User message: build_user_message() below. Its layout is frozen too, because
  adapters learn from these exact inputs. Only its contents vary.

What stays in plain code (never in the model): quote checks, the score, pass
or fail, and the risk tier. This keeps them deterministic and auditable.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROMPTS = ROOT / "app" / "llm" / "prompts"
SCHEMA_PATH = ROOT / "app" / "llm" / "schemas" / "call_review.json"
CLIENTS = ROOT / "data" / "clients"

LOW_CONFIDENCE = 0.7          # below this, a call goes to an analyst (ARCHITECTURE §3)
NEVER_NA = {"C3", "S4"}       # the prompt forbids "na" for these


@lru_cache(maxsize=None)
def load_client(client_id: str) -> dict:
    return json.loads((CLIENTS / f"{client_id}.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def system_prompt(client_id: str) -> str:
    return (PROMPTS / load_client(client_id)["prompt"]).read_text(encoding="utf-8").strip()


@lru_cache(maxsize=1)
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def schema_name(client_id: str) -> str:
    # Same convention as Redline's mubit_client.call(): task "review.thistle" -> "review_thistle"
    return load_client(client_id)["task"].replace(".", "_")


def build_user_message(client_id: str, utterances: list[dict], rules: list[dict], playbook_version: int) -> str:
    """utterances: [{speaker: "agent"|"customer", text, start_s}] (already redacted).
    rules: [{text, applies_when?}] for this client's review task, oldest first."""
    name = load_client(client_id)["name"].upper()
    lines = [f"PLAYBOOK ({name}, v{playbook_version})"]
    if rules:
        for i, r in enumerate(rules, 1):
            when = f" (applies when: {r['applies_when']})" if r.get("applies_when") else ""
            lines.append(f"{i}. {r['text']}{when}")
    else:
        lines.append("No rules yet.")
    lines += ["", "TRANSCRIPT"]
    for u in utterances:
        lines.append(f"[{float(u['start_s']):.1f}] {u['speaker'].upper()}: {u['text'].strip()}")
    return "\n".join(lines)


def _norm(s: str) -> str:
    s = s.lower().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"\s+", " ", s)
    return s.strip(" .,!?\"'")


def _check(evidence: list[dict], utterances: list[dict], where: str, issues: list[dict]) -> list[dict]:
    """Keep only quotes that really appear in the transcript; snap start_s to the matching line."""
    kept = []
    for ev in evidence:
        q = _norm(ev.get("quote", ""))
        hit = next((u for u in utterances if q and q in _norm(u["text"])), None)
        if hit is None:
            issues.append({"where": where, "issue": "quote not in transcript", "quote": ev.get("quote", "")})
            continue
        kept.append({"quote": ev["quote"], "start_s": float(hit["start_s"]), "speaker": hit["speaker"]})
    return kept


def verify_evidence(review: dict, utterances: list[dict]) -> tuple[dict, list[dict]]:
    """Hallucination guard: drop invented quotes. If a non-"na" item loses all its evidence, cap its confidence at 0.5."""
    issues: list[dict] = []
    r = json.loads(json.dumps(review))
    r["complaint"]["evidence"] = _check(r["complaint"]["evidence"], utterances, "complaint", issues)
    r["vulnerability"] = [
        {**v, "evidence": ev}
        for v in r["vulnerability"]
        if (ev := _check(v["evidence"], utterances, f"vulnerability.{v['driver']}", issues))
    ]
    for item_id, item in r["scorecard"].items():
        had = len(item["evidence"])
        item["evidence"] = _check(item["evidence"], utterances, item_id, issues)
        if item["answer"] != "na" and had and not item["evidence"]:
            item["confidence"] = min(item["confidence"], 0.5)
        if item["answer"] == "na" and item_id in NEVER_NA:
            issues.append({"where": item_id, "issue": "answered na, which the prompt forbids"})
            item["confidence"] = min(item["confidence"], 0.5)
    return r, issues


def score(review: dict, client_id: str) -> dict:
    """Deterministic scoring from the item answers. Returns the fields the API serves."""
    client = load_client(client_id)
    items = {i["id"]: i for i in client["items"]}
    card = review["scorecard"]

    critical_fails = [i for i, meta in items.items() if meta["kind"] == "critical" and card[i]["answer"] == "no"]
    scored = [i for i, meta in items.items() if meta["kind"] == "scored" and card[i]["answer"] != "na"]
    total = sum(items[i]["weight"] for i in scored)
    got = sum(items[i]["weight"] for i in scored if card[i]["answer"] == "yes")
    overall_pct = round(100 * got / total) if total else 100
    passed = not critical_fails and overall_pct >= client["pass_mark"]
    confidence = min(card[i]["confidence"] for i in items)

    vulnerable = bool(review["vulnerability"])
    if (vulnerable and card["C2"]["answer"] == "no") or len(critical_fails) >= 2:
        risk_tier = "critical"
    elif critical_fails:
        risk_tier = "high"
    elif not passed:
        risk_tier = "medium"
    else:
        risk_tier = "low"

    return {
        "overall_pct": overall_pct,
        "pass": passed,
        "critical_fails": critical_fails,
        "risk_tier": risk_tier,
        "confidence": round(confidence, 2),
        "low_confidence": confidence < LOW_CONFIDENCE,
    }
