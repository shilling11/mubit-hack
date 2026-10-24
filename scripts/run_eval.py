"""Run one or more drafting configurations on an RFP and print the scoreboard.

Usage:
  python -m scripts.run_eval --rfp meridian --compare base,latest
  python -m scripts.run_eval --rfp meridian --compare base,latest --model gpt-4o-mini

Every number comes from real Mubit calls scored against data/eval/gold_<rfp>.jsonl.
"""
import argparse
import time

from app import db
from app.learning import playbook
from app.models import RunIn
from app.pipeline import runner

METRICS = [
    ("status_accuracy", "Status accuracy", lambda v: f"{v:.1%}"),
    ("over_promises", "Over-promises", str),
    ("under_claims", "Under-claims", str),
    ("trap_correct", "Trap rows correct", str),
    ("citation_coverage", "Citation coverage", lambda v: f"{v:.1%}"),
    ("key_fact_coverage", "Key facts stated", lambda v: f"{v:.1%}" if v is not None else "—"),
    ("latency_p50_ms", "Latency p50 (ms)", str),
    ("tokens_out", "Output tokens", str),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rfp", default="meridian")
    ap.add_argument("--compare", default="base,latest", help="comma list of: base, latest, or a version number")
    ap.add_argument("--model", default=None)
    args = ap.parse_args()
    db.init()

    versions = []
    for c in args.compare.split(","):
        c = c.strip()
        versions.append(0 if c == "base" else playbook.latest_version() if c == "latest" else int(c))

    ids = [runner.start(RunIn(package=args.rfp, playbook_version=v, model=args.model))["id"] for v in versions]
    while any(runner.get(i)["status"] == "running" for i in ids):
        done = sum(runner.get(i)["done"] for i in ids)
        total = sum(runner.get(i)["total"] for i in ids)
        print(f"\r{done}/{total} drafted", end="", flush=True)
        time.sleep(2)
    print()

    runs = [runner.get(i) for i in ids]
    print(f"\n{'':22}" + "".join(f"{r['label'][:22]:>24}" for r in runs))
    for key, label, fmt in METRICS:
        vals = []
        for r in runs:
            s = r["score_json"] or {}
            v = s.get(key)
            if key == "trap_correct" and v is not None:
                vals.append(f"{v}/{s.get('trap_total')}")
            else:
                vals.append(fmt(v) if v is not None else "—")
        print(f"{label:22}" + "".join(f"{v:>24}" for v in vals))
    print("\nrun ids:", ", ".join(ids))


if __name__ == "__main__":
    main()
