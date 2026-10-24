"""Re-score practice calls at the latest playbook so Mubit gets corrected-behaviour training examples.

Mubit keeps only new examples, so this skips calls already reviewed at the
latest version. Held-out calls are never used.

Usage: python -m scripts.warm_mubit [--limit 80]
"""
import argparse
from concurrent.futures import ThreadPoolExecutor

from app import db
from app.config import MAX_PARALLEL
from app.learning import playbook
from app.review import service


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=200)
    args = ap.parse_args()
    db.init()
    v = playbook.latest_version()
    if v == 0:
        raise SystemExit("Playbook is at v0: load seeds or submit a correction first (base reviews are never training data).")
    done = {r["call_id"] for r in db.query("SELECT DISTINCT call_id FROM reviews WHERE playbook_version = ? AND record_mode = 'full'", (v,))}
    todo = [r["id"] for r in db.query("SELECT id FROM calls WHERE split = 'practice' ORDER BY id") if r["id"] not in done][: args.limit]
    if not todo:
        raise SystemExit(f"Every practice call is already reviewed at v{v}. Add a correction for a new version.")
    print(f"reviewing {len(todo)} practice calls at playbook v{v} (record=full)…")
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        out = list(pool.map(lambda cid: service.review_call(cid, v), todo))
    print(f"done: {sum(1 for r in out if not r.get('error'))} ok, {sum(1 for r in out if r.get('error'))} failed. "
          "Check Mubit console > Tasks for the kept-example count.")


if __name__ == "__main__":
    main()
