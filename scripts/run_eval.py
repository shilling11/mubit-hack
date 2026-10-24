"""Evaluate on the held-out calls: base vs the latest playbook, repeated, and print the comparison.

Usage: python -m scripts.run_eval [--repeats 3] [--versions 0,2]
Held-out reviews are always recorded as metadata (never trained on).
"""
import argparse
import time

from app import db
from app.eval import runner
from app.learning import playbook

ROWS = [("system_critical_recall", "Critical recall (system)", "pct"), ("false_negatives", "False negatives", "num"),
        ("model_critical_recall", "Critical recall (model)", "pct"), ("critical_precision", "Critical precision", "pct"),
        ("human_queue_rate", "Human queue rate", "pct"), ("item_accuracy", "Item accuracy", "pct"),
        ("complaint_recall", "Complaint recall", "pct"), ("vulnerability_recall", "Vulnerability recall", "pct"),
        ("latency_p50_ms", "Latency p50 (ms)", "num")]


def fmt(m: dict | None, kind: str) -> str:
    if not m:
        return "—"
    f = (lambda v: f"{v * 100:.0f}%") if kind == "pct" else (lambda v: f"{v:.1f}" if isinstance(v, float) and v % 1 else f"{v:.0f}")
    return f(m["mean"]) if m["min"] == m["max"] else f"{f(m['mean'])} ({f(m['min'])}–{f(m['max'])})"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--versions", default=None, help="comma list, default: 0 and latest")
    args = ap.parse_args()
    db.init()
    versions = [int(v) for v in args.versions.split(",")] if args.versions else sorted({0, playbook.latest_version()})
    ids = [runner.start("heldout", v)["id"] for _ in range(args.repeats) for v in versions]
    while any(db.one("SELECT status FROM runs WHERE id = ?", (i,))["status"] == "running" for i in ids):
        done = sum(db.one("SELECT done FROM runs WHERE id = ?", (i,))["done"] for i in ids)
        total = sum(db.one("SELECT total FROM runs WHERE id = ?", (i,))["total"] for i in ids)
        print(f"\r{done}/{total} reviewed", end="", flush=True)
        time.sleep(2)
    print()
    groups = runner.compare("heldout")
    print(f"{'':28}" + "".join(f"{g['label'] + ' ×' + str(g['runs']):>22}" for g in groups))
    for key, label, kind in ROWS:
        print(f"{label:28}" + "".join(f"{fmt(g['metrics'].get(key), kind):>22}" for g in groups))


if __name__ == "__main__":
    main()
