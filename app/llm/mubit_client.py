"""The ONLY module allowed to call a model. Every call goes through Mubit's gateway.

How Mubit sees our calls (README §3, verified 24 Oct 2026):
- A task is the set of calls sharing model + system prompt + tools + output format.
  Each Redress task has one fixed system prompt and one fixed JSON schema;
  everything that varies goes in the user message.
- `x-middleware-request-id` (mreq_...) is kept as the trace ID; `response.model`
  says which model served the call.
- `x-middleware-record`: "full" can become a training example; "metadata" is
  logged without content and never trained on (base and held-out reviews).
- No `metadata.session_id`: OpenAI rejects `metadata` unless `store` is on.
"""
import json
import time
from functools import lru_cache

from openai import APIStatusError, OpenAI

from app import db
from app.config import MUBIT_API_KEY, MUBIT_BASE_URL, MUBIT_MODEL


class MubitError(RuntimeError):
    def __init__(self, message: str, request_id: str | None = None):
        super().__init__(message)
        self.request_id = request_id


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    if not MUBIT_API_KEY:
        raise MubitError("MUBIT_API_KEY is not set. Add it to .env.")
    return OpenAI(base_url=MUBIT_BASE_URL, api_key=MUBIT_API_KEY, max_retries=3, timeout=180)


def call(
    task: str,
    system: str,
    user: str,
    schema: dict,
    *,
    call_id: str | None = None,
    run_id: str | None = None,
    record: str = "full",
    model: str | None = None,
    reasoning_effort: str | None = None,
) -> dict:
    """Route one structured-output call through Mubit and log a trace.

    `system` must be identical for every call of `task` (it defines the Mubit task).
    Returns {output, request_id, served_by, model_asked, latency_ms, tokens_in, tokens_out}.
    """
    model = model or MUBIT_MODEL
    kwargs: dict = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": task.replace(".", "_"), "strict": True, "schema": schema},
        },
        "extra_headers": {"x-middleware-record": record},
    }
    if reasoning_effort:
        kwargs["reasoning_effort"] = reasoning_effort
    t0 = time.perf_counter()
    trace = {"ts": time.time(), "task": task, "call_id": call_id, "run_id": run_id,
             "model_asked": model, "record_mode": record}

    def elapsed() -> int:
        return int((time.perf_counter() - t0) * 1000)

    try:
        raw = _client().chat.completions.with_raw_response.create(**kwargs)
        resp = raw.parse()
    except APIStatusError as exc:
        rid = exc.response.headers.get("x-middleware-request-id") if exc.response is not None else None
        db.insert("traces", {**trace, "request_id": rid, "ok": 0, "error": str(exc)[:500], "latency_ms": elapsed()})
        raise MubitError(str(exc), rid) from exc
    except Exception as exc:
        db.insert("traces", {**trace, "ok": 0, "error": str(exc)[:500], "latency_ms": elapsed()})
        raise MubitError(str(exc)) from exc

    usage = resp.usage
    result = {
        "request_id": raw.headers.get("x-middleware-request-id"),
        "served_by": resp.model,
        "model_asked": model,
        "latency_ms": elapsed(),
        "tokens_in": usage.prompt_tokens if usage else None,
        "tokens_out": usage.completion_tokens if usage else None,
    }
    fields = {k: result[k] for k in ("request_id", "served_by", "latency_ms", "tokens_in", "tokens_out")}
    content = resp.choices[0].message.content or ""
    try:
        result["output"] = json.loads(content)
    except json.JSONDecodeError as exc:
        db.insert("traces", {**trace, **fields, "ok": 0, "error": f"bad JSON: {content[:200]}"})
        raise MubitError(f"{task} returned invalid JSON", result["request_id"]) from exc
    db.insert("traces", {**trace, **fields, "ok": 1})
    return result
