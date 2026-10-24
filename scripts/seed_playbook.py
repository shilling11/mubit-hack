"""Load the guardrail seed corrections and build a playbook version from them.

Usage: python -m scripts.seed_playbook
"""
from app import db
from app.learning import corrections, playbook


def main() -> None:
    db.init()
    n = corrections.load_seed()
    if not n:
        print(f"seeds already loaded; playbook is at v{playbook.latest_version()}")
        return
    v = playbook.build(note="Guardrail seeds")
    print(f"loaded {n} seeds → playbook v{v['version']}")
    for r in v["rules_json"]:
        print(f"  {r['item_id']}: {r['rule']}")


if __name__ == "__main__":
    main()
