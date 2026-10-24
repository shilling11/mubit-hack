"""Test a rule on archived calls: re-score the calls it plausibly affects and show what changed."""
import re
from concurrent.futures import ThreadPoolExecutor

from app import db
from app.config import MAX_PARALLEL
from app.learning import playbook
from app.review import service

_pool = ThreadPoolExecutor(max_workers=MAX_PARALLEL, thread_name_prefix="archive")


def candidates(rule: dict, limit: int = 6) -> list[str]:
    """Practice and live calls whose transcript mentions the rule's keywords, most matches first."""
    words = [k.lower() for k in rule.get("keywords", []) if k.strip()]
    if not words:
        return []
    pat = re.compile("|".join(re.escape(w) for w in words), re.I)
    hits: dict[str, int] = {}
    for u in db.query("SELECT u.call_id, u.text_redacted FROM utterances u JOIN calls c ON c.id = u.call_id "
                      "WHERE c.split != 'heldout'"):
        n = len(pat.findall(u["text_redacted"]))
        if n:
            hits[u["call_id"]] = hits.get(u["call_id"], 0) + n
    return [cid for cid, _ in sorted(hits.items(), key=lambda x: -x[1])[:limit]]


def test_rule(correction_id: int, limit: int = 6) -> dict:
    """Re-score candidate calls at the latest playbook (which includes the rule) vs the version before it."""
    version = playbook.latest_version()
    rule = next((r for r in playbook.rules(version) if r["correction_id"] == correction_id), None)
    if rule is None:
        raise KeyError(f"no rule from correction {correction_id} in playbook v{version}")
    ids = candidates(rule, limit)
    prev = max(0, version - 1)

    def one(cid):
        before = service.review_call(cid, prev, run_id="archive", update_queue=False)
        after = service.review_call(cid, version, run_id="archive", update_queue=False)
        return cid, before, after

    changed = []
    for cid, before, after in _pool.map(one, ids):
        if not (before.get("items_json") and after.get("items_json")):
            continue
        for item_id, it in after["items_json"].items():
            b = before["items_json"][item_id]["answer"]
            if b != it["answer"]:
                changed.append({"call_id": cid, "item_id": item_id, "before": b, "after": it["answer"]})
    return {"rule": rule, "version": version, "tested": ids, "changed": changed}
