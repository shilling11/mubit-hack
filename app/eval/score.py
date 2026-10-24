"""Deterministic scoring of reviews against hand-checked gold labels (no LLM judge).

Gold rows (data/eval/gold.jsonl): {"call_id", "items": {"C1": "no", ...}, "complaint": bool, "vulnerability": bool}

A critical breach in gold is "caught" by the system when the model answered
"no", or when the call was routed to a human anyway (unsure, low confidence,
safety net). Missing it entirely is a false negative: the number we care
about most (README §9).
"""
import json
from statistics import median

from app.config import EVAL_DIR
from app.review.spec import items_by_id


def load_gold() -> dict[str, dict]:
    path = EVAL_DIR / "gold.jsonl"
    if not path.exists():
        return {}
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    return {r["call_id"]: r for r in rows}


def score_runs(reviews: list[dict], routes: dict[str, str], gold: dict[str, dict]) -> dict:
    """reviews: review rows; routes: call_id -> queue kind the routing would give."""
    defs = items_by_id()
    critical = [i for i, d in defs.items() if d["kind"] == "critical"]
    n_items = correct_items = 0
    breaches = model_caught = system_caught = 0
    flagged = flagged_true = 0
    complaint_pos = complaint_hit = vuln_pos = vuln_hit = 0
    to_human = 0
    per_call = []
    for r in reviews:
        g = gold.get(r["call_id"])
        if not g or not r.get("items_json"):
            continue
        items = r["items_json"]
        human = routes.get(r["call_id"]) in ("breach", "analyst")
        to_human += human
        call_fn = []
        for item_id in defs:
            got, want = items[item_id]["answer"], g["items"][item_id]
            n_items += 1
            correct_items += got == want
            if item_id in critical:
                if got == "no":
                    flagged += 1
                    flagged_true += want == "no"
                if want == "no":
                    breaches += 1
                    model_caught += got == "no"
                    caught = got == "no" or human
                    system_caught += caught
                    if not caught:
                        call_fn.append(item_id)
        out = r.get("output_json") or {}
        if g.get("complaint"):
            complaint_pos += 1
            complaint_hit += bool(out.get("complaint", {}).get("expressed"))
        if g.get("vulnerability"):
            vuln_pos += 1
            vuln_hit += bool(out.get("vulnerability"))
        per_call.append({"call_id": r["call_id"], "items_correct": sum(items[i]["answer"] == g["items"][i] for i in defs),
                         "false_negatives": call_fn, "to_human": human})
    n = len(per_call)
    lat = [r["latency_ms"] for r in reviews if r.get("latency_ms")]
    return {
        "calls": n,
        "item_accuracy": round(correct_items / n_items, 3) if n_items else None,
        "critical_breaches": breaches,
        "model_critical_recall": round(model_caught / breaches, 3) if breaches else None,
        "system_critical_recall": round(system_caught / breaches, 3) if breaches else None,
        "false_negatives": breaches - system_caught,
        "critical_precision": round(flagged_true / flagged, 3) if flagged else None,
        "human_queue_rate": round(to_human / n, 3) if n else None,
        "complaint_recall": round(complaint_hit / complaint_pos, 3) if complaint_pos else None,
        "vulnerability_recall": round(vuln_hit / vuln_pos, 3) if vuln_pos else None,
        "latency_p50_ms": int(median(lat)) if lat else None,
        "tokens": sum((r.get("tokens_in") or 0) + (r.get("tokens_out") or 0) for r in reviews),
        "per_call": per_call,
    }
