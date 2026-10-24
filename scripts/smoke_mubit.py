"""Check Mubit and Deepgram are reachable: one review of demo call 1 (record=off) and one Deepgram sample.

Usage: python -m scripts.smoke_mubit
"""
import json

from app.capture import stt
from app.demo import scripts
from app.llm.mubit_client import _client
from app.config import MUBIT_MODEL, REVIEW_REASONING_EFFORT
from app.privacy.redact import redact
from app.review import spec


def main() -> None:
    s = next(x for x in scripts() if x["id"] == "demo_call1")
    utts = [{**u, "text": redact(u["text"])} for u in s["utterances"]]
    kwargs = {"reasoning_effort": REVIEW_REASONING_EFFORT} if REVIEW_REASONING_EFFORT else {}
    raw = _client().chat.completions.with_raw_response.create(
        model=MUBIT_MODEL,
        messages=[{"role": "system", "content": spec.system_prompt()}, {"role": "user", "content": spec.build_user_message(utts, [], 0)}],
        response_format={"type": "json_schema", "json_schema": {"name": "review_call", "strict": True, "schema": spec.schema()}},
        extra_headers={"x-middleware-record": "off"}, **kwargs)
    items, issues = spec.verify(json.loads(raw.parse().choices[0].message.content), utts)
    print("Mubit OK:", raw.headers.get("x-middleware-request-id"), {k: v["answer"] for k, v in items.items()}, spec.score(items))
    r = stt.transcribe_url("https://dpgr.am/spacewalk.wav")
    print(f"Deepgram OK: {len(r['utterances'])} utterances, confidence {r['confidence']:.2f}")


if __name__ == "__main__":
    main()
