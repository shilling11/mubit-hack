# Redress: QA on every regulated call, with a model that learns from your analysts

> **Night Shift: $65K Mubit Hackathon, London** · 23–25 October 2026 · <https://luma.com/nightshift-london>
>
> **One-liner:** Banks check about 5% of customer calls by hand against a compliance scorecard, and the other 95% go unchecked. Redress scores **every** call through Mubit. Analysts stop filling in scorecards and instead **review and correct the AI's scorecard** on the calls they already sample. Every correction becomes a rule straight away and a Mubit model update over time, so the unreviewed calls get scored more accurately each week. Anything that might be a breach goes to a human: we'd rather ask than miss.
>
> **This README is the final architecture.** §3 is the Mubit knowledge we verified building our first prototype. Read it before touching any model call. The HTML files in [`design/`](design/) are visual references only (animated theme and graphics); their content predates this architecture.

---

## 0. How to use this README (teammates and coding agents)

- Build in the order in [§11 Build plan](#11-build-plan).
- **Hard rule: every LLM call goes through `app/llm/mubit_client.py`.** Speech-to-text (Deepgram) isn't an LLM task and calls Deepgram directly.
- **Freeze the system prompts and JSON schemas early.** Mubit identifies a task by its system prompt, model and output format; changing any of them starts a new task at zero training examples (§3.4).
- **Scores, pass/fail, routing and safety nets are plain code**, never the model. That keeps them deterministic and auditable.
- `TODO(verify)` marks things we haven't tested. Don't invent API details for Mubit, Deepgram or LiveKit. Check their docs.
- All customers, calls and bank data are **synthetic**. The two live demo callers are actors reading a script.

---

## 1. Vision

### The problem
Every regulated customer call (complaints, collections, fees, vulnerable customers) should meet the bank's compliance standards: identity checked, mandatory disclosures made, complaints recognised, vulnerability spotted and supported, no promises the bank can't keep, correct next steps. Today QA works like this:

1. Calls are recorded by the contact-centre system.
2. A **small random sample** goes to QA analysts. Team research (sources in the `bank` branch's `docs/QA_RESEARCH.md`; verify before quoting) found 1–2% to under 5% is typical in UK contact centres, and the FCA doesn't prescribe a percentage. We use **~5%** as our example.
3. An analyst **listens to the whole call** and fills in a **scorecard**: weighted items plus **critical (auto-fail) items**, with comments.
4. Analysts **calibrate** with each other regularly, because they disagree.
5. Failures lead to coaching, urgent remediation (a missed complaint must still be handled) and board reporting under Consumer Duty.

**What's wrong with it:** it's slow (an analyst can spend as long as the call itself on one review), it's inconsistent between analysts, and **~95% of calls are never checked**, so most breaches are never found.

### The insight
Analysts already make the judgement calls that matter: "that *was* a complaint even though she never said the word", "he mentioned his wife died, so that's vulnerability", "'I'm sure we'll refund it' is a promised outcome". Those judgements are the bank's real compliance standard, and today they live only in analysts' heads and calibration meetings.

### The solution
1. **Every call** is transcribed and scored against the bank's scorecard by a Mubit-routed model.
2. On the calls analysts would have sampled anyway, they **review the AI's scorecard** instead of starting from blank: confirm, or change an answer and give a one-line reason. That's faster than scoring from scratch.
3. Each correction becomes a **rule** (a playbook version), which every later review includes straight away. Over time the corrected reviews become **Mubit training examples**, so a small task model learns the bank's standard.
4. The other ~95% of calls are scored by the improving model. **Anything that might be a breach goes to a human**; confident breaches are flagged straight away.

**What stays human:** every escalated call, every audit-sample call, and every decision about a colleague. Redress drafts scores; people decide.

### Narrative for the judges (30 seconds)
> "Banks check one call in twenty. We check all of them. Two of us make a real phone call: one plays a Thistle Bank colleague, one a customer. Redress records it, transcribes it, and scores it against the bank's compliance scorecard through Mubit. The analyst corrects one thing the AI missed, in one line. A second, similar call comes in, and this time Redress catches it. Those corrections train a small Mubit model, so the 95% of calls nobody listens to are scored the way your best analyst would score them."

**Money line:** *Without Mubit, AI scores calls. With Mubit, it learns how your QA team scores them.*

---

## 2. Hackathon fit

| Item | Detail |
|---|---|
| Event | Night Shift: $65K Mubit Hackathon, London · Fri 23 Oct 17:00 → Sun 25 Oct 14:00 |
| Brief | Route LLM calls through Mubit; turn corrections into model updates for a recurring task |
| Freeze | **Sun 10:00** code freeze · 10:30 expo judging · 12:30 finalist demos · 13:30 awards |

| Track | How Redress fits |
|---|---|
| **1. Recurring tasks** (primary) | Scoring a call against a scorecard is the same job on every call, at contact-centre volume |
| **2. Own your intelligence layer** | Reviewing 100% of calls on a frontier model is expensive; a Mubit adapter does it cheaply. Shown as quality, latency and £ per 1,000 calls |
| **3. Fast refresh** | A new rule (e.g. a new mandatory disclosure from Monday) is taught with one correction and applies to the next call |

| Judging criterion | How Redress scores |
|---|---|
| **Use of Mubit** | A live correction becomes a rule and changes the next call's score; corrected reviews train a Mubit adapter (Try models). Every call visibly goes through Mubit |
| **Usefulness** | Regulated, high-volume, mostly unchecked today, with a real cost to missed breaches |
| **Technical execution** | Real-call transcription, evidence quotes with timestamps checked against the transcript, conservative routing, held-out gold labels, fixed-rule scoring, averaged runs |
| **Demo** | Two real people on a real call, live, then a second call showing the improvement (§10) |

---

## 3. Mubit: what we know, what we learned, and the traps

This section is everything we verified while building our first prototype, an RFP-response tool (24 Oct 2026), so nobody has to rediscover it. Sources: <https://docs.mubit.ai/llms-full.txt>, live calls with our key, and written answers from the Mubit team.

### 3.1 What Mubit is
Mubit is a **proxy** between your app and the model provider (OpenAI, Anthropic, Gemini, OpenRouter, Groq, Together, Mistral). You change the base URL and use a Mubit key, and nothing else in your code changes. Mubit:
1. passes each call to the provider and **records** it (request and reply, by default);
2. groups similar calls into **tasks**;
3. keeps some calls as **kept examples** (not every call is kept);
4. once a task has **25 kept examples**, trains an **adapter**: a small open model for that one task. It grades each version on how closely it matches **your provider model's answers**;
5. lets you compare a passing adapter with the provider model in the console's **Try models**.

The adapter learns to **copy the provider model on your inputs**. That's why our corrections reach the model: the playbook rules are part of the input, so the provider's corrected answers are what the adapter learns.

### 3.2 Verified API facts

| Fact | Detail |
|---|---|
| Base URLs | OpenAI SDK `https://api.mubit.ai/openai/v1` · Anthropic SDK `https://api.mubit.ai/anthropic` (no `/v1`) · Gemini `https://api.mubit.ai/gemini` |
| Key | Mubit key (`mbt_…`) passed as the SDK's API key. Send **only** the Mubit key: a provider key or an extra credential (e.g. a stray `ANTHROPIC_AUTH_TOKEN`) gets a `401` |
| Paths on starter credit | OpenAI: `/chat/completions`, `/responses`, `/embeddings`, `/models`. Anthropic: `/v1/messages`, `/v1/messages/count_tokens`, `/v1/models`. Anything else → `403 starter_credit_route` |
| Starter-credit models (our project) | OpenAI: `gpt-6-sol`, `gpt-6.1-sol`, `gpt-6-luna`, `gpt-6-astra`, `gpt-5.5`, `gpt-4o-mini`, `gpt-4.1-mini`. Anthropic: `claude-opus-5-5`, `claude-sonnet-5-5`, `claude-haiku-4-5`. Others → `400 starter_credit_model` (the error message lists the allowed ones) |
| Structured outputs | `response_format: {type: "json_schema", strict: true}` works through Mubit |
| Streaming | `stream: true` works, and Mubit passes the stream through |
| Request ID | Every response has header `x-middleware-request-id` (`mreq_…`). Read it with `client.chat.completions.with_raw_response.create(...)` |
| Who served it | `response.model` |
| What Mubit keeps | Header `x-middleware-record: full` (default; can become a training example) · `metadata` (logged without content, **never trained on, not listed in Requests**) · `off` |
| Sessions | Mubit takes `metadata.session_id` if sent, but **OpenAI rejects `metadata` unless `store=true`**, and we don't want OpenAI storing calls. Without it, Mubit derives the session from the instructions plus the first user message, so a multi-turn conversation that resends history stays one session |
| CORS | None. Call Mubit from the server, never from the browser |
| Limits | 10s to connect, 610s to first byte, 60 min total per call. The SDK owns retries |

### 3.3 What Mubit does **not** do (confirmed by the Mubit team)
- **No API for corrections or feedback.** Corrections are made in the Mubit console. A **Bad** rating does **not** remove a call from training; only `x-middleware-record: metadata` keeps a call out.
- **No way to call an adapter.** Adapters have no model ID, and the only place to run one is **Try models** in the console (a daily quota, about 3 adapter starts a day, and the first start can take minutes). "Mubit routes your live calls to the adapter" is **not** how it works today.
- **No custom grading.** A version is graded on how closely it matches the provider model's answers.
- A read-only key can read records but can't make calls. The console's "Figures unavailable … needs manager" message is a role permission on metrics, not an error in your calls.

### 3.4 How tasks form (this decides whether you ever get an adapter)
Calls are one task when they share **model + system prompt + tools + tool choice + output format**. Whitespace, numbers, dates and IDs in the system prompt don't split a task; other changing words do. Messages after the system prompt, `temperature` and `max_tokens` don't count.

Consequences we hit:
- **Same prompt, two models = two tasks.** Our draft task split into "Bid response writer" (`gpt-4o-mini`) and "Bid response writer 2" (`gpt-6-luna`). Pick **one model per task** and stick to it.
- **Editing a system prompt creates a new task** at 0 of 25. Freeze prompts by Saturday night, or the adapter never trains.
- **Put everything that varies in the user message** (case facts, transcript, policy passages, playbook rules), never in the system prompt.
- If a task uses tools, the **tool definitions** are part of the fingerprint. Keep the tool list fixed.
- **The scorecard is in the `review.call` system prompt**, so each bank's scorecard is its own task and its own adapter. Editing the scorecard starts a new task.

### 3.5 Kept examples, and why the count was slow
- Training starts at **25 kept examples**, and the console shows `Collecting examples` → `Reviewing examples` → `Training` → `Testing`.
- **Duplicates don't count.** Re-sending identical calls added nothing. We sent about 150 draft calls on one task and it sat at 23 kept for hours. New, varied inputs (a fresh practice RFP) got it to 25 and training started.
- The count updates **after** Mubit reviews examples, which can lag. Calls show up in the task's call count first.
- Waits are normal: daily training limit (resets 00:00 UTC), a pause between trainings, "too few examples" for test cases.
- Practical rule: **generate at least 40 varied synthetic cases per task early**, and send them with the final prompt and playbook.

### 3.6 Our integration pattern (reuse this)
```python
# app/llm/mubit_client.py: the only module that calls a model
client = OpenAI(base_url=MUBIT_BASE_URL, api_key=MUBIT_API_KEY, max_retries=3, timeout=180)

def call(task, user, schema, *, run_id=None, record="full", model=None) -> dict:
    raw = client.chat.completions.with_raw_response.create(
        model=model or MUBIT_MODEL,
        messages=[{"role": "system", "content": system_prompt(task)},   # fixed per task
                  {"role": "user", "content": user}],                    # everything that varies
        response_format={"type": "json_schema",
                         "json_schema": {"name": task.replace(".", "_"), "strict": True, "schema": schema}},
        extra_headers={"x-middleware-record": record},                   # "metadata" = never trained on
    )
    resp = raw.parse()
    # log a trace: task, raw.headers["x-middleware-request-id"], resp.model, latency, tokens
    return {"output": json.loads(resp.choices[0].message.content), "request_id": ..., "served_by": resp.model, ...}
```
Add trace logging (task, request ID, model, latency, tokens, record mode) and error handling around it.

### 3.7 The learning loop that works with Mubit as it really is
```text
Handler corrects a case + says why ──► correction record (our DB)
        │
        ├─► rule.induce (Mubit call) turns the reason into a general rule ──► playbook vN
        │
        ├─► IMMEDIATE: every later call includes playbook vN in the *user* message
        │              → the next complaint is handled with the rule
        │
        └─► MODEL UPDATE: practice-case calls with playbook vN are sent with record=full
                       → Mubit keeps them → 25 kept → adapter trains → shown in Try models
Base (v0) and held-out calls are sent with record=metadata → never training data
```

### 3.8 Lessons from our first prototype (measured, not guessed)
- **Don't trust chatbot answers about Mubit.** We were told about `record_outcome()`, `remember()`, `MINIMA_REFLECT_EVERY_N` and automatic adapter routing. The `mubit-sdk` package exists on PyPI, but its endpoints returned `unknown_route` on our gateway key, and the Mubit team confirmed there's no correction API and no adapter routing. Check the docs, then test with one call.
- **Current models rarely over-promise when the evidence is clear; they hedge.** `gpt-6-luna` got all the obvious traps right with no rules. Its real failure was answering "Partial" to things fully covered. Don't assume where the model fails: score the practice calls at base first, then write corrections and synthetic hard cases around the errors it actually makes.
- **A narrow rule set can make things worse** (80.8% vs base 86.6%), and a broad "don't hedge" rule once flipped "auto-approve payments" to Comply. **Guardrail rules** (seeded corrections for the non-negotiables) fixed it: 86.6% → **94.9%** averaged over 3 runs.
- **Single runs are noisy** (±1–2 rows out of 26). Quote averages over 3 runs with min–max ranges.
- **Held-out hygiene:** we accidentally sent our "held-out" set to Mubit with full recording and had to replace it. Make held-out cases `metadata`-only **in code**, not by remembering.
- **Latency (measured through Mubit, JSON output):** `gpt-6-luna` about 3–4s p50 per call; `gpt-4o-mini` and `gpt-4.1-mini` about 1.4s. Fine for post-call review (target: scorecard within 20s of hang-up). Longer transcripts mean longer calls: measure on a 90-second call.
- **Ops gotchas:** `uvicorn --reload` restarts kill in-flight background work, so demo without `--reload`. npm was broken under Git Bash on our Windows machine but works in PowerShell. Next.js versions before 16.4.1 had critical advisories, so we use 16.4.3.

---

## 4. How it works

### 4.1 The flow
```text
 Customer ⇄ Bank colleague          (demo: two people on a real call; production: the contact-centre recorder)
        │ recording (ideally one track per speaker)
        ▼
 ┌──────────────────────────────── Redress API (FastAPI, SQLite) ────────────────────────────────┐
 │ 1 CAPTURE     call audio saved locally · optional live captions (streaming STT)                │
 │ 2 TRANSCRIBE  Deepgram pre-recorded → utterances [agent | customer, start_s, end_s, confidence] │
 │ 3 SCRUB       PII redaction (plain code) before anything leaves the laptop for Mubit           │
 │ 4 REVIEW      review.call via Mubit → per-item answer + evidence quote + confidence            │
 │               evidence check (plain code): every quote must exist in the transcript            │
 │ 5 SCORE       plain code: weighted score, critical fails, pass/fail, risk tier                 │
 │ 6 ROUTE       plain code: breach → escalate · uncertain / safety net → analyst · 5% → audit    │
 │               · rest → auto-scored                                                              │
 │ 7 CORRECT     analyst confirms or changes each item + one-line reason → corrections             │
 │ 8 LEARN       rule.induce via Mubit → playbook vN → every later review includes the rules      │
 │               corrected-behaviour reviews (record=full) → Mubit kept examples → adapter         │
 │ app/llm/mubit_client.py ──────────────────────────────────► Mubit gateway ─► provider model    │
 └──────────────────────────────────────────────────────────────────────────────────────────────┘
        ▲ REST, polled every 1–2s (no WebSockets on venue Wi-Fi)
 Web app (Next.js): Wall · Live call · Queue · Evaluation form · Learning · Compare · Mubit panel
```

### 4.2 Call capture and transcription
**Assumption we can't work around: the audio is high-fidelity.** Every score depends on the transcript, and a misheard "I was in hospital" is a missed vulnerability. Real contact centres record calls cleanly, usually with **one track per speaker** (stereo). We design for that and say so openly.

| | Demo setup | Fidelity | Speaker labels |
|---|---|---|---|
| **A (recommended)** | Two people on two laptops (or a laptop and a phone browser) in a **call room** (LiveKit, WebRTC). Redress joins as a silent recorder and records **each track separately** | Best: each voice on its own clean track, headsets recommended | Exact, from the track |
| **B** (what we use) | An ordinary phone call on **speaker next to the laptop mic**; the caller stays out of the mic's range | Lower: one mixed track, room noise | Deepgram diarisation (turns split at 0.5s pauses) + **Swap speakers**, or click one line's speaker label to flip just that line, then **Re-score** |
| **Fallback** | A pre-recorded file of the same script, uploaded | Same as recorded | As recorded |

- **Transcription:** Deepgram **pre-recorded** API after hang-up is the source of truth (more accurate than streaming): punctuation, smart formatting, utterances with timestamps and confidence. Streaming captions during the call are a nice-to-have for the audience. `TODO(verify)`: current model name (Nova-3 or newer), `en-GB`, and whether Deepgram's own redaction options are available on our plan.
- **Low-confidence transcription is a routing signal.** If any utterance's STT confidence is below a threshold, or audio quality is poor, the call goes to an analyst: we don't score what we couldn't hear.
- Speech-to-text isn't an LLM call, so it goes to Deepgram directly. `TODO(verify)` with the Mubit team that this is acceptable under the brief.

### 4.3 PII scrubbing (before anything reaches Mubit)
Mubit **records request and reply content by default** (§3.2). Data is synthetic, but we build as a bank would:

1. **Redact in plain code before any model call:** card numbers (13–19 digits, with a Luhn check), sort codes, account numbers, dates of birth, postcodes, phone numbers, email addresses, and the customer's name and address from the (synthetic) customer record. Replace with typed tokens: `[CARD]`, `[DOB]`, `[NAME]` and so on. The review never needs the values: it needs to know that *an identity check happened*, not what the date of birth was.
2. **Keep raw audio and the raw transcript on the laptop only**, in the local store. Only redacted text is sent to Mubit.
   **The stored recording is redacted too:** the Live call page records 16 kHz WAV, and after transcription every word that fell inside a text redaction (date of birth, card, name, address…) is silenced in the saved file using Deepgram's word timestamps (`app/privacy/audio.py`). The evaluation form says how many moments were silenced. Compressed uploads (WebM, MP3) can't be edited without extra tools, so their audio isn't redacted. Names are redacted when they're in `data/customers.json` or typed in the **Customer** field on the Live call page.
3. **Show it:** the evaluation form can toggle "what Mubit saw" (the redacted transcript), and the Mubit console's Requests page shows the same.
4. **Record modes:** held-out and base runs use `x-middleware-record: metadata` (no content kept at Mubit). Production would add a provider key under the bank's own account and a data-processing agreement.
5. **ACL-gated memory:** our Mubit gateway key has **no memory endpoints**. The `mubit-sdk` memory calls returned `unknown_route` (§3.3), so we don't depend on memory or ACLs. Mubit does scope keys to one project, and read-only keys can read records but not make calls. `TODO(verify)`: ask the Mubit team whether access-controlled memory or per-client data isolation exists for our project.

### 4.4 The review (one Mubit task)
- **Task `review.call`:** the system prompt holds the reviewer instructions **and the bank's scorecard**, so it's fixed per bank. That makes one Mubit task, and one adapter, per bank (§3.4).
- **User message (varies):** the playbook rules (vN) + the redacted transcript as `[start_s] AGENT|CUSTOMER: text`.
- **Output (strict JSON):** for every scorecard item: `answer` (`yes` / `no` / `na` / `unsure`), short `reasoning`, `evidence` quotes with timestamps, and `confidence` (0–1). Plus `complaint {expressed, category, evidence}`, `vulnerability [{driver, evidence}]` and a short `summary`.
- **Plain code afterwards:** every quote is checked against the transcript (quotes that don't exist are dropped, and the item is re-marked `unsure`). Then the weighted score, critical fails, pass/fail and risk tier are computed.

### 4.5 Conservative by design: false negatives are the danger
A missed breach (scored as compliant when it wasn't) is far worse than an extra human review. So the system leans conservative, **on critical items only**, and budgets human time so it stays useful.

| Mechanism | Rule (plain code) |
|---|---|
| **Pass needs positive evidence** | A critical item can only be `yes` (compliant) with a quote showing the compliant behaviour, e.g. the identity check *before* account details. No quote → `unsure` |
| **`unsure` is allowed and routed** | The prompt tells the model to say `unsure` rather than guess on critical items. Any critical `unsure` → analyst |
| **Confidence threshold** | Any critical item with confidence < **0.8**, or any scored item < **0.6** → analyst |
| **Keyword safety net** | Independent of the model: vulnerability cues ("hospital", "passed away", "can't afford", "lost my job", "carer"…) and complaint cues ("not happy", "unacceptable", "want to complain"…). If a cue fires and the model says no vulnerability or no complaint → analyst |
| **STT quality** | Low transcription confidence or poor audio → analyst |
| **Confident breach** | A critical item `no` with evidence and confidence ≥ 0.8 → **flagged as a breach**, escalated immediately (it still gets a human check, but it's surfaced first) |
| **Audit sample** | A random **5%** of calls go to an analyst whatever the model says. This is the sample banks already take, and it keeps our accuracy figures honest (it's not chosen by the model) |
| **Everything else** | Auto-scored, counted in coverage and reporting |

**Not obnoxiously conservative:** we track the **human queue rate** (the share of calls sent to analysts) next to **critical recall**. The target is to catch every breach in the held-out set while sending well under a third of calls to humans. Thresholds are tuned on practice calls, never on the held-out set. Per-item agreement is tracked; an item whose AI-vs-analyst agreement stays high over many audited calls can earn auto-accept for that item only.

### 4.6 The analyst's job: review the AI, don't redo it
1. Open a call from the queue: the transcript (with audio playback from any timestamp), and the AI scorecard pre-filled with answers, quotes and confidence. Critical items are pinned to the top.
2. For each item: **✓ agree**, or **change the answer** and give a one-line reason (a dropdown of common reasons, or free text).
3. Submit. Each changed item becomes a **correction**; agreements count towards per-item agreement.

### 4.7 The learning loop (how corrections become model updates)
See §3.7 for why it works this way with Mubit.
```text
Analyst correction (before, after, reason)
   ├─► rule.induce (Mubit) → a general rule → playbook vN
   ├─► IMMEDIATE: every later review.call includes playbook vN in the user message → the next call is scored with the rule
   └─► MODEL UPDATE: reviews made with vN on practice and live calls are sent with record=full
                     → Mubit keeps them → 25 kept → adapter trains → compare in Try models
Base (v0) reviews and held-out calls are sent with record=metadata → never training data
```
- **The 5% audited calls** are where corrections come from: the analysts' existing workload, now faster.
- **The 95% unreviewed calls** benefit from every rule straight away, and from the adapter once it passes.
- **"Test on archive":** when a rule is added, re-score the archived calls it plausibly affects and show what changed (before → after). This is how a QA lead checks a rule before trusting it.
- **Guardrail rules:** seed a few non-negotiables (e.g. "a promised refund before investigation is always a C3 fail") so a broad rule can't loosen a critical item. On our first prototype, a broad rule without guardrails made results worse (§3.8).

---

## 5. The scorecard (Thistle Bank, fictional)
Adapted from the team's QA research (scorecard structure: weighted items plus critical auto-fails).

| # | Item | Type | Basis |
|---|---|---|---|
| C1 | Complaint recognised and logged, even if the word "complaint" wasn't used | **Critical** | FCA DISP definition of a complaint |
| C2 | Vulnerability recognised and support offered | **Critical** | FCA FG21/1 (health, life events, resilience, capability) |
| C3 | No promise of an outcome and no misleading statement | **Critical** | Consumer Duty: consumer understanding |
| C4 | Identity verified before account details were discussed | **Critical** | Bank security policy |
| S1 | Next steps and the right timescale explained (8 weeks, or 15 business days for payment services) | 20 pts | FCA DISP 1.6 |
| S2 | Checked the customer understood | 20 pts | Consumer Duty: consumer understanding |
| S3 | Information given was accurate | 20 pts | Bank policy |
| S4 | Empathy and tone | 20 pts | Service standard |
| S5 | Took ownership and agreed a follow-up | 20 pts | Service standard |

**Pass** = no critical fail and a score of 80 or more. The scorecard lives in `data/scorecard.json` and is written into the `review.call` system prompt (so editing it starts a new Mubit task: freeze it early). Regulatory references are summaries: verify before quoting on stage.

---

## 6. Mubit tasks
| Task | System prompt (fixed) | User message (varies) | Output (strict JSON) | Record mode |
|---|---|---|---|---|
| `review.call` | Reviewer instructions + the bank's scorecard (`app/llm/prompts/review_call.md`) | Playbook vN + redacted transcript | Per-item answer, reasoning, evidence, confidence; complaint; vulnerability; summary | Practice + live calls with vN ≥ 1: `full` · base v0 and held-out: `metadata` |
| `rule.induce` | Rule writer (`app/llm/prompts/rule_induce.md`) | Correction: item, before, after, reason, transcript excerpt | `{rule, applies_when, keywords}` | `full` |
| `data.generate` (offline, optional) | Synthetic call writer | A scenario spec (§9) | A transcript | `metadata` (not a product task) |

One fixed model for `review.call` and `rule.induce` (`MUBIT_MODEL`); never mix models within a task (§3.4).

---

## 7. Data model and API

### SQLite tables
```text
calls(id, source:"live"|"upload"|"synthetic", split:"practice"|"heldout"|"live", agent_name, audio_path, duration_s,
      stt_confidence, created_at)
utterances(call_id, idx, speaker:"agent"|"customer", text_raw, text_redacted, start_s, end_s, confidence)
reviews(id, call_id, playbook_version, request_id, model, record_mode, latency_ms, tokens_in, tokens_out,
        output_json, score, pass, critical_fails, risk_tier, created_at)
queue(call_id, kind:"breach"|"analyst"|"audit"|"auto", reasons_json, due_at, done)
evaluations(id, call_id, review_id, analyst, items_json, comments, submitted_at)
corrections(id, call_id, review_id, item_id, before, after, reason, created_at)
playbook_versions(version, created_at, correction_ids, rules_json)
agreement(item_id, n, agreed, pct, updated_at)
eval_runs(id, label, playbook_version, model, metrics_json, per_call_json, created_at)
traces(ts, task, call_id, request_id, model, served_by, record_mode, latency_ms, tokens_in, tokens_out, ok, error)
```

### API (FastAPI, `app/main.py`)
```text
GET  /api/status                    Mubit/Deepgram config, playbook version, pending corrections, trace counts
GET  /api/scorecard                 the scorecard (data/scorecard.json)
POST /api/calls                     multipart {audio, agent_name} → {call_id}   (background: Deepgram → redact → review → route)
POST /api/calls/import              {split, review, calls:[{id?, agent_name, utterances:[{speaker, text, start_s, end_s?}]}]}
POST /api/demo/scripts/{id}         load demo_call1 / demo_call2 as a text call and review it (rehearsal and fallback)
GET  /api/calls?split=              list with queue kind, score, risk tier
GET  /api/calls/{id}                call + utterances (raw and redacted) + latest review (items with labels) + queue + evaluation
GET  /api/calls/{id}/audio          the recording, for playback from a timestamp
POST /api/calls/{id}/review?playbook_version=   re-score now (e.g. the same call at an older version, side by side)
POST /api/calls/{id}/swap-speakers  fix speaker labels, then re-review
POST /api/calls/{id}/evaluation     {items:[{id, answer, reason}], comments} → corrections + new playbook version + rules
GET  /api/wall                      coverage stats + one tile per call
GET  /api/queue                     open breach / analyst / audit items, most urgent first
GET  /api/learning                  playbook versions, rules, corrections, per-item agreement
POST /api/corrections/seed          load guardrail seeds and build a playbook version
POST /api/rules/{correction_id}/test?limit=   test on archive: re-score affected calls, before vs after
POST /api/eval                      {repeats, versions?} → held-out runs (always metadata)
GET  /api/runs · GET /api/compare   run progress · averaged metrics per playbook version
GET  /api/traces?limit=             Mubit trace panel
POST /api/demo/reset                clear live calls and analyst corrections (keeps synthetic calls and seed playbook)
```

---

## 7b. The web app (Next.js, `web/`)
Styled after Abdul's HTML references in `design/`: the corridor background with light streaks, the pixel voice glyph, word-by-word blur reveals, glass cards that light where the cursor is, glowing lime cards, the beam and the Mubit particle morph. Everything is live from the API (polled every 1–5s).

| Page | What it's for |
|---|---|
| `/` **Landing** (our slide deck) | Scroll or use ↑/↓ and 1–5: **Home** → **Problem** (100-tile wall: 5 heard today, click *Score them all* or press L to flip to 100%) → **How it works** (the 7-step pipeline and the 4 critical items) → **Proof** (live held-out numbers and per-call barcode) → **Mubit** (particle morph: collecting → training → adapter passed; click to step) → **Open the dashboard** |
| `/dashboard` **Overview** | Stats, the wall (one tile per call, coloured by risk; audit sample outlined), the queue (breach / analyst / audit, most urgent first), quick buttons to load the demo calls as text |
| `/dashboard/live` **Live call** | **Record call** (laptop mic, live equaliser), **Stop & score** → Deepgram → Mubit → scorecard. Shows "scored in Xs after hang-up", the four finding cards lighting up (complaint, vulnerable, critical fails, routed), the transcript, **Upload file** and **Swap speakers** |
| `/dashboard/calls/[id]` **Evaluation form** | The analyst's screen: transcript (▶ plays the audio from any line; flagged lines glow), *What Mubit saw* toggle (redacted), the AI scorecard with critical items first, quotes, confidence and routing reasons. Pick pass / fail / n/a / unsure, give a one-line reason (preset suggestions offered), **Submit & teach** → the induced rule and the new playbook version, **Test this rule on archived calls**, and **Compare with v0 / previous version** side by side |
| `/dashboard/learning` | Playbook versions, rules (newest lit), corrections feed, AI-vs-analyst agreement per item, test any rule on the archive, load the guardrail seeds |
| `/dashboard/proof` | Held-out metrics per playbook version (mean and min–max), per-call barcode, **Run 3× base vs latest** |
| `/dashboard/mubit` | Gateway settings, training examples sent, adapter stages, live trace table (task, record mode, request ID, latency, tokens) |

---

## 8. Technology and repo layout

| Layer | Choice | Notes |
|---|---|---|
| LLM gateway | **Mubit**, OpenAI SDK, one base URL | `review.call`, `rule.induce`; strict JSON; one fixed model |
| Speech-to-text | **Deepgram** pre-recorded (+ optional streaming captions) | Timestamps, confidence, diarisation for setup B |
| Call room (demo setup A) | **LiveKit** (Cloud free tier), WebRTC | A silent recorder participant records each track. `TODO(verify)`: LiveKit Agents API for a non-publishing participant and track recording |
| Backend | Python 3.11, FastAPI, Pydantic, SQLite, httpx | Single laptop; polled by the UI |
| Frontend | Next.js 16.4.3, React 19, Tailwind 4 | Styled after `design/` (dark, lime accent, Inter Tight, animated background) |

```text
mubit-hack/
├── README.md                     # this file (final architecture)
├── design/                       # HTML prototypes: visual reference only (theme, graphics, motion)
├── .env.example · requirements.txt
├── app/                          # FastAPI (to build)
│   ├── main.py · config.py · db.py
│   ├── llm/mubit_client.py       # ONLY model gateway (pattern in §3.6)
│   ├── llm/prompts/              # review_call.md, rule_induce.md (frozen early)
│   ├── llm/schemas/              # call_review.json (strict)
│   ├── capture/                  # upload, LiveKit recorder hook, Deepgram transcription, speaker labelling
│   ├── privacy/redact.py         # PII scrubbing
│   ├── review/                   # spec.py (user message, evidence check, score), route.py (§4.5), safety_net.py
│   ├── learning/                 # corrections.py, playbook.py, test_on_archive.py
│   └── eval/                     # score.py (vs gold), compare.py
├── data/
│   ├── scorecard.json            # Thistle's scorecard
│   ├── customers.json            # synthetic customer records (used for redaction and the demo script)
│   ├── calls/practice/*.json     # synthetic transcripts for corrections and Mubit warm-up
│   ├── calls/heldout/*.json      # never trained on (record=metadata)
│   ├── eval/gold.jsonl           # held-out labels, written before any run
│   ├── corrections/seed.jsonl    # guardrail corrections
│   └── demo/                     # the two live-call scripts + a fallback recording
├── scripts/                      # generate_calls.py, import_calls.py, warm_mubit.py, run_eval.py, smoke_mubit.py, reset_demo.py
└── web/                          # Next.js app
```

---

## 9. Synthetic data and evaluation

### Synthetic transcripts (to train and to test)
- **Label-first generation:** write a **scenario spec** per call (customer situation, what the colleague does right or wrong per scorecard item), then generate the transcript from it. The spec *is* the gold label. Spot-check every held-out call by hand.
- **Mix:** ~80 practice calls (Mubit warm-up, corrections, the wall) + ~25 held-out calls (gold, `metadata` only). About 40% contain a hard case: a complaint without the word "complaint", vulnerability mentioned in passing, a promised refund, the wrong deadline, account details before the identity check, or a clean call that *looks* risky (to measure over-flagging).
- **Variety matters for Mubit:** duplicates aren't kept as training examples (§3.5), so vary customers, wording, products and length.

### Metrics (fixed rules vs gold, averaged over 3 runs with min–max)
| Metric | Why |
|---|---|
| **Critical recall** (and the false negative count) | The headline. A missed breach is the worst outcome |
| Critical precision | Over-flagging costs analyst time |
| **Human queue rate** | Conservatism has a price; keep it bounded |
| Per-item accuracy and agreement | Where the model and analysts differ |
| Complaint recall, vulnerability recall | The two items most often missed by people |
| Latency per call, £ per 1,000 calls | Track 2: provider model vs adapter |

---

## 10. Demo (3 minutes, live)

**Cast:** Abdul plays **Sam**, a Thistle Bank colleague, and answers his phone **on speaker next to the laptop**. Sultan plays the customer and rings him. The laptop runs Redress on the projector and records the room. Scripts: [`data/demo/call1.json`](data/demo/call1.json) (Abdul's) and [`data/demo/call2.json`](data/demo/call2.json).

### Before going on stage
1. `python -m scripts.reset_demo` (keeps the 80 scored practice calls and the guardrail playbook; clears live calls and analyst corrections).
2. Start the API **without** `--reload`, then the web app (§12). Open `http://localhost:3000` full-screen in Chrome; allow the microphone once on `/dashboard/live`.
3. Recommended: in rehearsal, make the S3 correction on call 1 (below), then **Proof → Run 3× base vs latest** so the latest playbook has averaged numbers. Don't reset after that; the live correction on stage then becomes the next version.
4. Mubit console open in another tab on **Tasks → Adapters**; if a version has **Passed**, start it once in **Try models** beforehand.
5. Rehearse both calls 3× in the room; upload the best take of each as a fallback (**Upload file** on the Live call page). If audio fails, **Demo call 1/2 (text)** loads the scripts instantly.

### What the rehearsal showed
The base model catches every planted lapse; where it differs from an analyst, it **over-flags**: S3 (accurate information) fails on call 1 because of the refund promise that C3 already counts. So the live correction is about **scoring like the bank's analysts**:

> *"Score each mistake under the one item it belongs to. A promised refund is a C3 fail, not inaccurate information: S3 is only for factually wrong statements about fees, rules or timescales."* (one click: it's a preset under S3)

### On stage, step by step
| Time | Do this | What the audience sees |
|---|---|---|
| 0:00–0:20 | Landing page: **Home** then **Problem**. Press **L** to flip the wall | "Banks hear one call in twenty." 5 tiles become 100 |
| 0:20–0:30 | Press **3** (How it works), then click **Open the dashboard** → **Live call** | The pipeline, then the live-call stage |
| 0:30–1:05 | Click **Record call**. Sultan rings Abdul; they play call 1. Click **Stop & score** | Timer and equaliser while recording; on stop, the beam runs and the four cards light: complaint, vulnerable (health), critical fails C1·C2·C3, routed: escalate |
| 1:05–1:35 | **Open the evaluation form**. Show the quotes (▶ plays the audio), *What Mubit saw*. On **S3** click **pass**, click the preset reason, **Submit & teach** | Rule appears; playbook v(N+1) |
| 1:35–2:10 | Back to **Live call**, record call 2 (Daniel, bereaved, card payment). **Stop & score** → evaluation form → **Compare with v(N)** | At the new version C3 passes, S3 fails (8 weeks should be 15 business days), C1 and C2 fail: scored like an analyst. Side by side with the earlier version |
| 2:10–2:35 | **Proof** | Held-out: every breach caught, 0 missed, precision and queue rate, per-call barcode |
| 2:35–2:52 | **Mubit** page, then the Mubit console's **Try models** | Training examples sent, trace table; the adapter vs the provider |
| 2:52–3:00 | Landing page **Mubit** section | "Without Mubit, AI scores calls. With Mubit, it learns how your QA team scores them." |

**Judge questions to prepare:**
- *What if the transcript is wrong?* → We assume high-fidelity recordings (contact centres record per speaker); low STT confidence routes the call to a human instead of scoring it. **Swap speakers** fixes a mislabelled call.
- *What about false negatives?* → 0 missed out of 22 breaches on the held-out set across 8 runs. Critical items need positive evidence to pass; `unsure` goes to a human; an independent keyword safety net; a 5% random audit.
- *Isn't this an LLM judging people?* → It drafts scores; analysts decide. Coaching and any action on a colleague stay human.
- *PII?* → Redacted in code before Mubit (toggle *What Mubit saw*); raw audio never leaves the laptop; held-out runs aren't stored at Mubit.
- *Isn't this just a prompt?* → The playbook applies corrections immediately; Mubit distils the corrected reviews into a task adapter (Try models).

---

## 11. Build plan
Code freeze is **Sun 10:00**.

| # | Task | Status |
|---|---|---|
| 1 | Mubit client (§3.6), config, SQLite, traces | ✅ |
| 2 | `scorecard.json`, `review_call.md`, `call_review.json`, `spec.py` (**frozen**) | ✅ |
| 3 | Redaction + evidence check + score + routing + safety net | ✅ |
| 4 | Synthetic practice (80) + held-out (25) calls and gold; import | ✅ gold labels need a human check (`data/eval/gold.jsonl`) |
| 5 | Evaluation → corrections → `rule.induce` → playbook; test on archive | ✅ |
| 6 | Deepgram upload path (setup B) | ✅ ~9s for a 26s recording |
| 7 | Mubit warm-up: 80 practice reviews at v1 (`record=full`) | ✅ sent; check Tasks → Adapters |
| 8 | Held-out eval, repeated | ✅ 4× base and 4× v1 (§15) |
| 9 | UI: landing, overview (wall + queue), live call (recorder), evaluation form, learning, proof, Mubit | ✅ §7b |
| 10 | Rehearse both calls 3×, record fallbacks, tune thresholds on practice calls | 🔲 **Before Sun 10:00** |

---

## 12. Setup
```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env                                         # MUBIT_API_KEY, DEEPGRAM_API_KEY
.\.venv\Scripts\python -m scripts.smoke_mubit                 # Mubit + Deepgram reachable?
.\.venv\Scripts\python -m uvicorn app.main:app --port 8000     # no --reload when demoing
cd web; npm install; npm run dev                               # http://localhost:3000 = landing · /dashboard = the app (PowerShell)
start design\prototype.html                                    # visual reference
```

**Data and evaluation scripts** (the generated transcripts are in the repo; a fresh database needs steps 2–3):
```powershell
.\.venv\Scripts\python -m scripts.generate_calls --only-missing   # 1. synthetic transcripts via Mubit (data.generate, metadata)
.\.venv\Scripts\python -m scripts.seed_playbook                   # 2. guardrail seeds → playbook v1
.\.venv\Scripts\python -m scripts.import_calls                    # 3. import all calls; score practice calls at the latest playbook
.\.venv\Scripts\python -m scripts.warm_mubit                      # re-score practice calls at a new playbook version (training examples)
.\.venv\Scripts\python -m scripts.run_eval --repeats 3            # held-out: base vs latest, averaged
.\.venv\Scripts\python -m scripts.reset_demo                      # before a demo run
```
Keys go in `.env` only. Provider keys (OpenAI or Anthropic) never go in the app: they live in the Mubit console under **Provider keys**. `REVIEW_REASONING_EFFORT` (default `low`) trades latency for depth: measured ~18.6s per review at the default effort, ~13.5s at `low`, ~10s at `none`.

---

## 13. Caveats and risks
| Caveat | How we handle it |
|---|---|
| **High-fidelity audio is assumed** | Stated openly; per-speaker tracks in the demo; low STT confidence → human |
| **False negatives** | §4.5: positive evidence to pass, `unsure`, thresholds, safety net, random audit, critical recall as the headline |
| **Over-flagging** | Queue rate tracked; thresholds tuned on practice calls; per-item auto-accept only after sustained agreement |
| **PII** | §4.3: redaction before Mubit, raw data local, `metadata` for held-out |
| **Mubit limits** | No correction API; adapters only in Try models; prompt edits reset tasks; kept-example lag (§3.3–3.5) |
| **LLM judging people** | Scores are drafts; humans decide; quotes and timestamps make every score auditable |
| **Regulatory summaries** | Our DISP / Consumer Duty / FG21/1 summaries are simplified; verify before quoting |

## 14. Ethics and data
- 100% synthetic customers and calls; live demo callers are actors reading a script.
- Redress assists QA; it never takes action on a colleague or a customer by itself.
- Recording notice: "this call is recorded for quality and training".

---

## 15. Status and measured results (25 Oct 2026)
**Held-out: 25 calls containing 22 critical breaches (18 calls with at least one), 4 runs per version:**

| | Base (v0) | Playbook v1 (guardrail seeds) |
|---|---|---|
| Breaches caught (system critical recall) | **100%** (100–100) | **100%** (100–100) |
| Missed breaches | **0** in every run | **0** in every run |
| Model critical recall (model said "fail") | 100% | 100% |
| Flag precision | 89.9% (88–96) | 89.0% (85–92) |
| Sent to a human | 81% (80–84) | 78% (76–84) |
| Item accuracy vs gold | 90.9% (91–92) | 90.9% (89–92) |
| Review time (median) | ~12s | ~12s |

- **What it means:** the model never missed a breach in 8 runs (22 breaches × 8 = 176 chances), so the conservative design isn't costing recall. The guardrail seeds (v1) cover things the base model already did right, so v1 ≈ base: the differences are within run-to-run noise. The room to improve is **precision and item accuracy** (over-flagging, mainly S3). That's what analyst corrections like the S3 rule should move; evaluate the version that includes it.
- **The queue rate is high because the synthetic set is lapse-dense** (18 of 25 calls genuinely breach). In a real centre most calls are compliant, so far fewer reach a human.
- **Mubit:** 88 full-record `review.call` examples sent (practice reviews at v1 plus rehearsal); base and held-out runs are metadata-only.
- **To check by hand:** the 25 held-out gold labels in `data/eval/gold.jsonl` (spec-derived) and the call 2 script.
