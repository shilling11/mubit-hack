"""Smoke-test the frozen review task before 00:00: one call through Mubit, checked and scored.

    python -m scripts.try_review                         # demo call, Thistle, record=metadata (never trained on)
    python -m scripts.try_review --dry-run               # offline: lint the schema, print the user message, score the gold answer
    python -m scripts.try_review --client northwind --call data/calls/<file>.json
    python -m scripts.try_review --record full           # only for varied practice calls you WANT as training examples

This calls Mubit's gateway directly with the same request shape as app/llm/mubit_client.py
(system prompt + user message + strict json_schema named after the task + x-middleware-record),
so it hits the same Mubit task the app will use. The app itself must call through mubit_client.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

from app.review import spec

ROOT = spec.ROOT
MUST_MATCH = ["C1", "C2", "C3", "C4", "S1", "S5"]


def load_env() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.split("#", 1)[0].strip().strip("'\""))


def lint_strict(node: dict, path: str = "$") -> list[str]:
    """OpenAI strict mode: every object lists all its properties as required and forbids extras."""
    errs = []
    if node.get("type") == "object":
        props = set(node.get("properties", {}))
        if node.get("additionalProperties") is not False:
            errs.append(f"{path}: additionalProperties must be false")
        if set(node.get("required", [])) != props:
            errs.append(f"{path}: required must list every property")
    for key in ("properties", "$defs"):
        for name, child in node.get(key, {}).items():
            errs += lint_strict(child, f"{path}.{name}")
    if isinstance(node.get("items"), dict):
        errs += lint_strict(node["items"], f"{path}[]")
    return errs


def report(review: dict, client_id: str, utterances: list[dict], expected: dict | None) -> None:
    checked, issues = spec.verify_evidence(review, utterances)
    s = spec.score(checked, client_id)
    items = {i["id"]: i for i in spec.load_client(client_id)["items"]}
    print(f"\nRESULT  {s['overall_pct']}%  {'PASS' if s['pass'] else 'FAIL'}  risk={s['risk_tier']}  "
          f"critical_fails={s['critical_fails']}  min_confidence={s['confidence']}")
    print(f"complaint={checked['complaint']['expressed']} ({checked['complaint']['category']})  clock={checked['clock']}  "
          f"vulnerability={[v['driver'] for v in checked['vulnerability']]}")
    for item_id, it in checked["scorecard"].items():
        q = it["evidence"][0]["quote"] if it["evidence"] else ""
        mark = ""
        if expected:
            want = expected["scorecard"][item_id]["answer"]
            mark = "  ok" if want == it["answer"] else f"  EXPECTED {want}" + ("  <-- must match" if item_id in MUST_MATCH else "")
        print(f"  {item_id} {items[item_id]['label'][:38]:38} {it['answer']:3} {it['confidence']:.2f}  \"{q[:60]}\"{mark}")
    print(f"summary: {checked['summary']}")
    if issues:
        print("evidence issues:", json.dumps(issues, indent=1))
    if expected:
        misses = [i for i in MUST_MATCH if expected["scorecard"][i]["answer"] != checked["scorecard"][i]["answer"]]
        misses += ["clock"] if expected["clock"] != checked["clock"] else []
        misses += ["complaint"] if expected["complaint"]["expressed"] != checked["complaint"]["expressed"] else []
        print("MUST-MATCH:", "all good" if not misses else f"MISSED {misses}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", default="thistle")
    ap.add_argument("--call", default="data/calls/demo_call.json")
    ap.add_argument("--record", default="metadata", choices=["metadata", "full", "off"])
    ap.add_argument("--rules", default=None, help="JSON file: [{text, applies_when}]")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    call = json.loads((ROOT / args.call).read_text(encoding="utf-8"))
    rules = json.loads((ROOT / args.rules).read_text(encoding="utf-8")) if args.rules else []
    user = spec.build_user_message(args.client, call["utterances"], rules, playbook_version=len(rules))
    expected_path = (ROOT / args.call).with_suffix(".expected.json")
    expected = json.loads(expected_path.read_text(encoding="utf-8")) if expected_path.exists() else None

    errs = lint_strict(spec.schema())
    print("schema strict-mode lint:", "ok" if not errs else errs)
    print(f"task={spec.load_client(args.client)['task']}  schema_name={spec.schema_name(args.client)}  "
          f"system_prompt={len(spec.system_prompt(args.client))} chars")
    print("\n--- user message ---\n" + user + "\n--------------------")

    if args.dry_run:
        if expected:
            print("\n[dry run] scoring the gold answer:")
            report({k: v for k, v in expected.items() if not k.startswith("_")}, args.client, call["utterances"], expected)
        return 0

    load_env()
    from openai import OpenAI  # imported here so --dry-run works without the SDK

    client = OpenAI(base_url=os.environ.get("MUBIT_BASE_URL", "https://api.mubit.ai/openai/v1"),
                    api_key=os.environ["MUBIT_API_KEY"], max_retries=2, timeout=180)
    model = os.environ.get("MUBIT_MODEL", "gpt-6-luna")
    t0 = time.perf_counter()
    raw = client.chat.completions.with_raw_response.create(
        model=model,
        messages=[{"role": "system", "content": spec.system_prompt(args.client)},
                  {"role": "user", "content": user}],
        response_format={"type": "json_schema",
                         "json_schema": {"name": spec.schema_name(args.client), "strict": True, "schema": spec.schema()}},
        extra_headers={"x-middleware-record": args.record},
    )
    resp = raw.parse()
    ms = int((time.perf_counter() - t0) * 1000)
    u = resp.usage
    print(f"\nmubit request_id={raw.headers.get('x-middleware-request-id')}  served_by={resp.model}  "
          f"latency={ms}ms  tokens_in={u.prompt_tokens if u else '?'}  tokens_out={u.completion_tokens if u else '?'}  "
          f"record={args.record}")
    report(json.loads(resp.choices[0].message.content), args.client, call["utterances"], expected)
    return 0


if __name__ == "__main__":
    sys.exit(main())
