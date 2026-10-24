"""Send corrected-behaviour draft calls through Mubit so the rfp.draft_response
task reaches its kept-example threshold (25 by default) and trains an adapter.

Uses the latest playbook on the practice packages (Northstar + Kestrel), never
on the held-out Meridian pack. Watch progress in the Mubit console under Tasks.

Usage: python -m scripts.warm_mubit [--rounds 1]
"""
import argparse
import time

from app import db
from app.learning import playbook
from app.models import RunIn
from app.pipeline import runner

PRACTICE = ["northstar", "kestrel"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=1)
    args = ap.parse_args()
    db.init()
    version = playbook.latest_version()
    if version == 0:
        raise SystemExit("Build a playbook first (Learning tab): warm-up should teach corrected behaviour, not the base.")
    for n in range(args.rounds):
        ids = [runner.start(RunIn(package=p, playbook_version=version))["id"] for p in PRACTICE]
        while any(runner.get(i)["status"] == "running" for i in ids):
            time.sleep(2)
        sent = sum(runner.get(i)["total"] for i in ids)
        print(f"round {n + 1}: sent {sent} rfp.draft_response calls with playbook v{version}")
    print("Check Mubit console > Tasks for the kept-example count and training status.")


if __name__ == "__main__":
    main()
