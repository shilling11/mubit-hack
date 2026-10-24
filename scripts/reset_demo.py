"""Clear live calls, evaluations, corrections and playbooks before a demo run.

Usage: python -m scripts.reset_demo [--all]   (--all also clears synthetic calls, runs and traces)
"""
import sys

from app import db
from app.main import reset


def main() -> None:
    db.init()
    print(reset(keep_synthetic="--all" not in sys.argv))


if __name__ == "__main__":
    main()
