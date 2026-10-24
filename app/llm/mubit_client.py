"""The ONLY module allowed to call a model. Every call goes through Mubit's gateway.

How Mubit sees our calls (docs.mubit.ai, verified 2026-10-24):
- Mubit forms a *task* from calls that share model + system prompt + output
  format. So each Redline task has one fixed system prompt (app/llm/prompts/)
  and one fixed JSON schema, and everything that varies per call (the
  requirement, evidence, playbook rules) goes in the user message.
- Each answer carries `x-middleware-request-id` (mreq_...), which we keep as the
  trace ID. `response.model` tells us which model actually served the call.
- `x-middleware-record` controls what Mubit keeps: "full" (default; the call
  can become a kept example for adapter training) or "metadata" (logged without
  content, never trained on). We use "metadata" for baseline runs so the
  uncorrected answers don't become training examples.
- We don't send `metadata.session_id`: OpenAI rejects `metadata` unless
  `store` is on, and we don't want OpenAI storing these calls. Mubit then
  derives the session from the conversation start, which is fine here.
"""
import json
import time
from functools import lru_cache
from pathlib import Path

from openai import APIStatusError, OpenAI

from app import db
from app.config import MUBIT_API_KEY, MUBIT_BASE_URL, MUBIT_MODEL

PROMPTS = Path(__file__).parent / "prompts"

TASKS = {
    "rfp.extract_requirements": "extract_requirements.md",
    "rfp.draft_response": "draft_response.md",
    "rfp.verify_claims": "verify_claims.md",
    "rfp.induce_rule": "induce_rule.md",
    "rfp.exec_summary": "exec_summary.md",
}


class MubitError(RuntimeError):
    def __init__(self, message: str, request_id: str | None = None):
        super().__init__(message)
        self.request_id = request_id


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    if not MUBIT_API_KEY:
        raise MubitError("MUBIT_API_KEY is not set. Add it to .env.")
    return OpenAI(base_url=MUBIT_BASE_URL, api_key=MUBIT_API_KEY, max_retries=3, timeout=180)


@lru_cache(maxsize=None)
def system_prompt(task: str) -> str:
    return (PROMPTS / TASKS[task]).read_text(encoding="utf-8").strip()


def call(
    task: str,
    user: str,
    schema: dict,
    *,
    run_id: str | None = None,
    record: str = "full",
    model: str | None = None,
) -> dict:
    """Route one structured-output call through Mubit and log a trace.

    Returns {output, request_id, served_by, model_asked, latency_ms, tokens_in, tokens_out}.
    """
    model = model or MUBIT_MODEL
    kwargs: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt(task)},
            {"role": "user", "content": user},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": task.replace(".", "_"), "strict": True, "schema": schema},
        },
        "extra_headers": {"x-middleware-record": record},
    }

    t0 = time.perf_counter()
    trace = {"ts": time.time(), "task": task, "run_id": run_id, "model_asked": model, "record_mode": record}
    try:
        raw = _client().chat.completions.with_raw_response.create(**kwargs)
        resp = raw.parse()
    except APIStatusError as exc:
        rid = exc.response.headers.get("x-middleware-request-id") if exc.response is not None else None
        db.insert("traces", {**trace, "request_id": rid, "ok": 0, "error": str(exc)[:500],
                             "latency_ms": int((time.perf_counter() - t0) * 1000)})
        raise MubitError(str(exc), rid) from exc
    except Exception as exc:
        db.insert("traces", {**trace, "ok": 0, "error": str(exc)[:500],
                             "latency_ms": int((time.perf_counter() - t0) * 1000)})
        raise MubitError(str(exc)) from exc

    latency_ms = int((time.perf_counter() - t0) * 1000)
    request_id = raw.headers.get("x-middleware-request-id")
    usage = resp.usage
    result = {
        "request_id": request_id,
        "served_by": resp.model,
        "model_asked": model,
        "latency_ms": latency_ms,
        "tokens_in": usage.prompt_tokens if usage else None,
        "tokens_out": usage.completion_tokens if usage else None,
    }
    content = resp.choices[0].message.content or ""
    try:
        result["output"] = json.loads(content)
    except json.JSONDecodeError as exc:
        db.insert("traces", {**trace, **_trace_fields(result), "ok": 0, "error": f"bad JSON: {content[:200]}"})
        raise MubitError(f"{task} returned invalid JSON", request_id) from exc

    db.insert("traces", {**trace, **_trace_fields(result), "ok": 1})
    return result


def _trace_fields(r: dict) -> dict:
    return {k: r[k] for k in ("request_id", "served_by", "latency_ms", "tokens_in", "tokens_out")}
