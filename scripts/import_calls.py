"""Import generated transcripts into the database and (optionally) score them.

Usage: python -m scripts.import_calls [--no-review] [--split practice|heldout]

Practice calls are reviewed at the current playbook (base v0 is recorded as
metadata; v1+ as full, so they become Mubit training examples). Held-out calls
are imported but only reviewed by evaluation runs (always metadata).
"""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor

from app import db
from app.capture import ingest
from app.config import CALLS_DIR, MAX_PARALLEL
from app.review import service


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-review", action="store_true")
    ap.add_argument("--split", choices=["practice", "heldout"], default=None)
    args = ap.parse_args()
    db.init()
    splits = [args.split] if args.split else ["practice", "heldout"]
    ids = {"practice": [], "heldout": []}
    for split in splits:
        for p in sorted((CALLS_DIR / split).glob("*.json")):
            c = json.loads(p.read_text(encoding="utf-8"))
            ids[split].append(ingest.create_call(c["utterances"], source="synthetic", split=split,
                                                 agent_name=c["agent_name"], call_id=c["id"]))
        print(f"imported {len(ids[split])} {split} calls")
    if args.no_review or not ids["practice"]:
        return
    print(f"reviewing {len(ids['practice'])} practice calls through Mubit…")
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        reviews = list(pool.map(lambda cid: service.review_call(cid), ids["practice"]))
    errors = [r for r in reviews if r.get("error")]
    kinds = db.query("SELECT kind, COUNT(*) AS n FROM queue GROUP BY kind")
    print(f"done: {len(reviews) - len(errors)} scored, {len(errors)} failed · queue: "
          + ", ".join(f"{k['kind']}={k['n']}" for k in kinds))


if __name__ == "__main__":
    main()
