"""Deterministic scoring of a run against hand-written gold labels (no LLM judge)."""
from statistics import median

RANK = {"Not Applicable": 0, "Do Not Comply": 1, "Partially Comply": 2, "Comply": 3}


def score_row(d: dict, g: dict) -> dict:
    acceptable = g.get("acceptable") or [g["status"]]
    status = d.get("status")
    text = f"{d.get('response') or ''} {d.get('gaps') or ''}".lower()
    facts = g.get("key_facts") or []
    facts_hit = [f for f in facts if any(alt in text for alt in f.split("|"))]
    cited = set(d.get("evidence_ids") or [])
    return {
        "req_id": d["req_id"],
        "gold_status": g["status"],
        "acceptable": acceptable,
        "status": status,
        "status_ok": status in acceptable,
        "over_promise": status is not None and RANK.get(status, 0) > max(RANK[a] for a in acceptable),
        "under_claim": status is not None and RANK.get(status, 0) < min(RANK[a] for a in acceptable),
        "trap": bool(g.get("trap")),
        "facts_total": len(facts),
        "facts_hit": len(facts_hit),
        "cited_ok": bool(cited & set(g["evidence_any"])) if g.get("evidence_any") else bool(cited),
        "note": g.get("note"),
    }


def score_run(drafts: list[dict], gold: dict[str, dict]) -> dict:
    rows = [score_row(d, gold[d["req_id"]]) for d in drafts if d["req_id"] in gold and d.get("status")]
    n = len(rows)
    if not n:
        return {"n": 0, "rows": {}}
    traps = [r for r in rows if r["trap"]]
    facts_total = sum(r["facts_total"] for r in rows)
    latencies = [d["latency_ms"] for d in drafts if d.get("latency_ms")]
    return {
        "n": n,
        "status_accuracy": round(sum(r["status_ok"] for r in rows) / n, 3),
        "over_promises": sum(r["over_promise"] for r in rows),
        "under_claims": sum(r["under_claim"] for r in rows),
        "trap_correct": sum(r["status_ok"] for r in traps),
        "trap_total": len(traps),
        "citation_coverage": round(sum(r["cited_ok"] for r in rows) / n, 3),
        "key_fact_coverage": round(sum(r["facts_hit"] for r in rows) / facts_total, 3) if facts_total else None,
        "flagged": sum("over_promise_risk" in (d.get("flags") or []) for d in drafts),
        "latency_p50_ms": int(median(latencies)) if latencies else None,
        "tokens_in": sum(d.get("tokens_in") or 0 for d in drafts),
        "tokens_out": sum(d.get("tokens_out") or 0 for d in drafts),
        "rows": {r["req_id"]: r for r in rows},
    }
