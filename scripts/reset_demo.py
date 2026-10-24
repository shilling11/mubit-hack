"""Clear runs, drafts, traces, corrections and playbook versions for a clean demo.

Usage: python -m scripts.reset_demo [--keep-traces]
"""
import sys

from app import db


def main() -> None:
    db.init()
    tables = ["runs", "drafts", "corrections", "playbook_versions"]
    if "--keep-traces" not in sys.argv:
        tables.append("traces")
    for t in tables:
        db.execute(f"DELETE FROM {t}")
    print(f"cleared: {', '.join(tables)}")


if __name__ == "__main__":
    main()
