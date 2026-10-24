# Redress: bank complaints that resolve better with every correction

> **Night Shift: $65K Mubit Hackathon, London** · 23–25 October 2026 · <https://luma.com/nightshift-london>
>
> **One-liner:** A bank's customer calls or emails with a complaint. A live voice agent takes the call, and Redress triages it, decides the outcome under the bank's policy and drafts the resolution email. Every model call goes through Mubit. When a complaints handler corrects a case, the fix becomes a rule straight away and a Mubit model update over time, so the next complaint is handled right first time.
>
> This replaces our first idea, **Redline** (RFP responses). Its full README, with everything we measured, is in [docs/redline/README.md](docs/redline/README.md), and its code is in commit `fb545f9`. **§3 below is the Mubit knowledge we learned building it. Read it before touching any model call.**

---

## 0. How to use this README (for teammates and coding agents)

- Build in the order in [§10 Build plan](#10-build-plan-ruthlessly-prioritised). The email path and the learning loop come first; the live voice agent is the highest-risk piece, so it gets a fallback.
- **Hard rule: every LLM call goes through `app/llm/mubit_client.py`** (the Mubit gateway). The only exceptions are speech-to-text and text-to-speech, which aren't LLM tasks.
- **Freeze system prompts and JSON schemas early.** Mubit identifies a task by its system prompt, model, tools and output format. Changing any of them starts a new task with zero training examples (§3.4).
- Anything marked `TODO(verify)` hasn't been tested by us yet. Don't invent API details for Mubit, Pipecat, Deepgram, Twilio or Resend. Check their docs.
- All customers, banks, accounts and complaints are **synthetic**. No real customer data, ever: Mubit records request and reply content by default.

---

## 1. Problem overview and narrative

### The problem
UK banks handle very large volumes of complaints, by phone and by email: unexpected fees, card disputes, scams, mortgage errors, poor service. Every complaint is regulated. The FCA's complaint rules (DISP) set the clock and the content:

| Rule (FCA DISP, summarised: verify before quoting) | What it means operationally |
|---|---|
| Resolved by the end of the **third business day** after receipt | A short "summary resolution communication" can close it, and must tell the customer about the Financial Ombudsman Service (FOS) |
| Otherwise a **final response within 8 weeks** | Must say whether the complaint is upheld, explain why, set out any redress, and give FOS referral rights (6 months) |
| **Payment services** complaints (e.g. card payments, transfers) | Shorter clock: **15 business days**, up to 35 in exceptional cases |
| Fair treatment, Consumer Duty, vulnerable customers | Vulnerability must be spotted and acted on; outcomes must be consistent |

Each case is the **same recurring task**:

> *Listen → work out what happened → classify it and start the right clock → spot vulnerability → decide uphold / partial / reject under policy → calculate redress → write a compliant, human response.*

Where it goes wrong today:

| Failure | Cost |
|---|---|
| Vulnerability missed ("I was in hospital", "my husband just died") | Unfair outcome, regulatory breach, reputational damage |
| Wrong clock (a card-payment dispute treated as 8 weeks, not 15 business days) | Missed deadline, automatic breach |
| Inconsistent redress: two handlers, two answers | Unfair treatment; the customer goes to the Ombudsman, and the bank pays a case fee |
| Letters missing FOS rights or a clear explanation | Non-compliant final response |
| Generic AI chatbots | Fluent but inconsistent; they either promise refunds the policy doesn't allow or hedge on clear-cut cases |

### The insight
Complaints handlers already **correct** cases all day, and those corrections are the bank's real policy in practice:

- "Fees charged while the customer was in hospital are refunded in full, plus a distress-and-inconvenience payment."
- "Card-payment disputes are payment-services complaints: 15 business days, not 8 weeks."
- "Never tell a scam victim the money will definitely come back before the investigation."

Today those corrections stay in one handler's head, or a QA spreadsheet.

### The solution
**Redress** answers the phone with a live voice agent, reads complaint emails, and drafts the whole case: triage, decision, redress and the resolution email. A human handler approves every outcome. Every model call goes through **Mubit**. Each correction a handler makes:
1. **immediately** becomes a playbook rule that the next case's calls include, and
2. **over time** becomes a Mubit task adapter: the corrected calls are Mubit's training examples, so a small, fast model learns the bank's complaint judgement.

### Narrative for the judges (30 seconds)
> "A customer rings Thistle Bank, upset: they were charged overdraft fees while they were in hospital. Our voice agent takes the call live. Redress triages it, starts the right regulatory clock and drafts the resolution email, all through Mubit. The handler spots what the AI missed, the vulnerability, and corrects it once. Seconds later a different customer's email complaint, which the system has never seen, is handled correctly first time. Those corrections train a small Mubit adapter, so this judgement runs on a model the bank owns."

**Money line:** *Without Mubit, the agent answers complaints. With Mubit, it learns how your bank resolves them.*

---

## 2. Hackathon info

| Item | Detail |
|---|---|
| Event | Night Shift: $65K Mubit Hackathon in London |
| Format | 42-hour overnight hackathon, around 500 builders |
| Dates | Fri 23 Oct 2026, 17:00 → Sun 25 Oct 2026, 14:00 (clocks go back on Sunday) |
| Prizes | 1st $15,000 · 2nd $10,000 · 3rd $5,000 · $35,000 AI credits · $1.5M Mubit credits |

**Brief:** build a product that routes its LLM calls through Mubit (one base-URL change) and turns corrections into model updates for a recurring task.

**Tracks (top 3 judged across all):** 1) **Recurring tasks** ← primary; 2) **Own your intelligence layer** (closed model vs task-adapted open model: quality, cost, latency) ← shown on the Compare tab; 3) **Fast refresh** (keeping pace with change) ← a policy change ("new fee-refund rule from Monday") taught with one correction.

| Judging criterion (equal weight) | How Redress scores |
|---|---|
| **Use of Mubit**: a correction becoming a model update | Live correction → rule → unseen complaint handled right; corrected calls → Mubit adapter, shown in Try models. Every call visibly routed through Mubit |
| **Usefulness**: a real recurring task | Bank complaints: regulated, high-volume, costly when wrong |
| **Technical execution** | Live voice pipeline, structured outputs, held-out set with hand-written gold labels, fixed-rule scoring, averaged runs |
| **Demo** | A live phone-style call plus a real email arriving, in 3 minutes (§9) |

| When | What |
|---|---|
| **Sun 10:00** | **Code freeze, submissions close** |
| Sun 10:30 | Judging round 1 (expo) |
| Sun 12:30 | Finalist demos on stage |
| Sun 13:30 | Awards |

---

## 3. Mubit: what we know, what we learned, and the traps

This section is everything we verified while building Redline (24 Oct 2026), so nobody has to rediscover it. Sources: <https://docs.mubit.ai/llms-full.txt>, live calls with our key, and written answers from the Mubit team.

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
- For the voice agent, the **tool definitions** are part of the fingerprint. Fix the tool list.

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
`git show fb545f9:app/llm/mubit_client.py` has the full version, with trace logging and error handling.

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

### 3.8 Lessons from Redline (measured, not guessed)
- **Don't trust chatbot answers about Mubit.** We were told about `record_outcome()`, `remember()`, `MINIMA_REFLECT_EVERY_N` and automatic adapter routing. The `mubit-sdk` package exists on PyPI, but its endpoints returned `unknown_route` on our gateway key, and the Mubit team confirmed there's no correction API and no adapter routing. Check the docs, then test with one call.
- **Current models rarely over-promise when the evidence is clear; they hedge.** `gpt-6-luna` got all the obvious traps right with no rules. Its real failure was answering "Partial" to things fully covered. Expect the same with complaints: the interesting errors will be **missed vulnerability, wrong clock and inconsistent redress**, not wild promises. Design the synthetic cases around those.
- **A narrow rule set can make things worse** (80.8% vs base 86.6%), and a broad "don't hedge" rule once flipped "auto-approve payments" to Comply. **Guardrail rules** (seeded corrections for the non-negotiables) fixed it: 86.6% → **94.9%** averaged over 3 runs.
- **Single runs are noisy** (±1–2 rows out of 26). Quote averages over 3 runs with min–max ranges.
- **Held-out hygiene:** we accidentally sent our "held-out" pack to Mubit with full recording and had to replace it. Make held-out cases `metadata`-only **in code**, not by remembering.
- **Latency (measured through Mubit, JSON output):** `gpt-6-luna` about 3–4s p50 per call; `gpt-4o-mini` and `gpt-4.1-mini` about 1.4s. Too slow for voice unless streamed and kept short (§5.3).
- **Ops gotchas:** `uvicorn --reload` restarts kill in-flight background work, so demo without `--reload`. npm was broken under Git Bash on our Windows machine but works in PowerShell. Next.js versions before 16.4.1 had critical advisories, so we use 16.4.3.

---

## 4. Product overview

### Channels
| Channel | Flow |
|---|---|
| **Phone (live voice agent "Ava")** | Customer calls → Ava greets, runs a light identity check (synthetic), listens, empathises, asks follow-ups, looks up recent transactions (tool), logs the complaint, sets expectations (timeline, next contact), says an email is coming. A live transcript and triage card fill in as the call happens |
| **Email** | A complaint email arrives in the demo inbox (seeded, or real inbound `TODO(verify)`) → same triage, decision and letter pipeline |

### Case pipeline (every LLM step is a Mubit task)
| # | Mubit task | Input (user message) | Output (strict JSON) | Recurring? Corrected by handler? |
|---|---|---|---|---|
| 1 | `complaint.voice_turn` | Conversation so far + case facts + tool results | Next spoken reply (short) + optional tool call | Every turn · rarely (tone, wording) |
| 2 | `complaint.triage` | Transcript or email + customer profile + playbook | Category, product, **regulatory clock**, **vulnerability flags + evidence quote**, severity, customer's ask, summary | Every case · **yes, core** |
| 3 | `complaint.decide` | Triage + transaction facts + policy passages + playbook | Outcome (upheld / partially / not upheld), reasons, **redress lines** (refunds, D&I payment), confidence | Every case · **yes, core** |
| 4 | `complaint.letter` | Case + decision + letter type + playbook | Email subject + body (summary resolution or final response), required-elements checklist | Every case · yes (wording, FOS rights) |
| 5 | `rule.induce` | Correction + handler's reason | One general rule + when it applies + keywords | Every correction |

Plain code, no LLM: identity check, clock and deadline arithmetic (from the triaged category), PII redaction, policy retrieval (BM25), the letter compliance checklist, and scoring.

### The handler workspace (web app)
- **Live call view:** live captions (customer / Ava), the triage card filling in, the clock started, vulnerability flags appearing with the quote that triggered them.
- **Case queue:** calls and emails, deadline countdowns, status.
- **Case view:** triage, decision and redress, draft email, evidence (transcript lines, transactions, policy passages). Edit anything, give a reason → **Teach** or **Teach & ripple**. **Approve & send** sends the real email.
- **Learning:** corrections (tracked-changes diffs), playbook versions, induced rules.
- **Compare:** held-out complaints, base vs playbook, averaged over 3 runs: triage accuracy, vulnerability recall, clock accuracy, outcome accuracy, redress within tolerance, letter-compliance pass rate, latency, cost.
- **Mubit trace panel:** every call with task, request ID, model, latency and record mode.

---

## 5. Architecture and technologies

### 5.1 Diagram
```text
 Customer (browser mic on stage / phone via Twilio at the expo)
        │ audio
        ▼
 ┌──────────────────────── Voice service (Pipecat, Python) ────────────────────────┐
 │  transport (WebRTC or Twilio Media Streams)                                      │
 │    → VAD (Silero) → STT streaming (Deepgram) ── interim + final transcript ──┐    │
 │    → LLM: complaint.voice_turn via Mubit (stream, fixed tools)              │    │
 │    → TTS streaming (Cartesia or ElevenLabs) → audio back to caller          │    │
 └─────────────────────────────────────────────────────────────────────────────┼────┘
        tool calls: lookup_customer · get_transactions · log_complaint · end_call   │ transcript events (WebSocket)
        ▼                                                                         ▼
 ┌──────────────────────────────── Redress API (FastAPI) ───────────────────────────┐
 │ cases · transcripts · PII redaction · policy retrieval (BM25) · deadlines        │
 │ post-call / email pipeline: triage → decide → letter (Mubit tasks)               │
 │ corrections → rule.induce → playbook vN · ripple · scoring · SQLite              │
 │ app/llm/mubit_client.py ───────────────► Mubit gateway ──► provider model        │
 │ email out (Resend or SMTP) only after the handler approves                       │
 └──────────────────────────────────────────────────────────────────────────────────┘
        ▲ REST + WebSocket (live captions, case updates)
 ┌──────┴─────── Web app (Next.js 16 + Tailwind 4) ───────┐
 │ live call · case queue · case view · learning ·         │
 │ compare · Mubit trace panel                             │
 └─────────────────────────────────────────────────────────┘
```

### 5.2 Stack
| Layer | Choice | Why / notes |
|---|---|---|
| Voice orchestration | **Pipecat** (Python, open source) | Cascade pipeline (VAD → STT → LLM → TTS) with interruption handling, OpenAI-compatible LLM service (point `base_url` at Mubit), WebRTC and Twilio transports. Alternative: LiveKit Agents. `TODO(verify)`: exact service and transport classes for the installed version |
| Speech-to-text | **Deepgram** streaming (Nova family) | Low-latency interim results for captions, endpointing, punctuation. Alternative: AssemblyAI streaming |
| Text-to-speech | **Cartesia** or **ElevenLabs** streaming | Fast first audio, natural UK voice. `TODO(verify)`: voice ID with a British accent |
| VAD / turn-taking | Silero VAD (via Pipecat) | Detects when the caller stops; supports barge-in |
| Telephony | Browser WebRTC for the stage demo; **Twilio** phone number + Media Streams for the expo | A browser mic avoids venue phone-signal risk; a real number lets judges call it themselves |
| LLM gateway | **Mubit**, OpenAI SDK, one base URL | All five tasks. Voice turns use a fast model (`gpt-4.1-mini` or `gpt-4o-mini`); case tasks use one model each, fixed (§3.4) |
| Backend | Python 3.11, FastAPI, Pydantic, SQLite, rank-bm25 | Reuse Redline modules (§6) |
| Email out | **Resend** API, or SMTP with an app password | Real email to the presenter's phone on stage. Human approval required |
| Email in | Seeded demo inbox; optional inbound webhook (Resend or Postmark inbound) `TODO(verify)` | The seeded inbox is enough for the demo |
| Frontend | Next.js 16.4.3, React 19, Tailwind 4, lucide-react | Reuse Redline's components, trace panel and diff view |

### 5.3 Voice design decisions
- **Cascade (STT → LLM → TTS), not speech-to-speech.** OpenAI's Realtime API is a WebSocket path that isn't on Mubit's served routes, so a speech-to-speech model would bypass Mubit entirely: no training examples and a broken brief. With a cascade, every reasoning turn is a Mubit call **and** we get clean text transcripts for triage and training.
- **Latency budget (target under 1.5s from the caller stopping to Ava speaking):** endpointing ~300ms + LLM first token (measure through Mubit, `TODO(verify)`) + TTS first audio ~200ms. Keep voice turns **short and streamed**, use a small model, keep the system prompt short, and push heavy work (triage, decision, letter) to **after** the call or to background calls during it.
- **Ava's job is to listen, not decide.** On the call Ava gathers facts, shows empathy, checks identity (synthetic), looks things up and sets expectations. She never promises a refund or an outcome; the decision comes from `complaint.decide` and a human approves it. This is safer and makes the call shorter.
- **Live triage during the call:** every few customer turns, the API runs `complaint.triage` in the background on the transcript so far and pushes updates to the UI. After the call, it runs once more on the final transcript. Mid-call triage calls are sent with `metadata` so only the final one is a training example.
- **Transcription:** interim results drive live captions; final segments, tagged by speaker (customer vs Ava, known from the pipeline), are stored with timestamps. Vulnerability flags quote the exact transcript line.
- **PII:** Mubit stores content by default. Data is synthetic, but we still redact card numbers, sort codes, account numbers and dates of birth by regex before any Mubit call (and show this to judges).
- **Barge-in:** if the caller interrupts, TTS stops and the turn restarts (Pipecat handles this; test it).
- **Fallbacks:** (1) a text-chat mode using the same `voice_turn` task; (2) a pre-recorded caller audio file fed through the same pipeline; (3) a recorded video.

### 5.4 Regulatory clock (plain code, from triage output)
| Triage category | Clock | Deadline |
|---|---|---|
| Resolved by end of 3rd business day | Summary resolution | Day 3 (business days) |
| Payment services (card payment, transfer, direct debit) | PSR | 15 business days (35 exceptional) |
| Everything else | DISP final response | 8 weeks |

UK bank holidays in the business-day calculation: `TODO(verify)`.

---

## 6. Repo layout (planned)
```text
mubit-hack/
├── README.md                       # this file
├── docs/redline/README.md          # previous idea: full context + measured results
├── .env.example
├── requirements.txt
├── app/                            # FastAPI
│   ├── main.py                     # REST + WebSocket (captions, case updates)
│   ├── config.py · db.py · models.py
│   ├── llm/
│   │   ├── mubit_client.py         # ONLY model gateway (reuse from fb545f9)
│   │   └── prompts/                # voice_turn, triage, decide, letter, induce_rule (frozen early)
│   ├── cases/                      # intake (call/email), redaction, deadlines, policy retrieval
│   ├── pipeline/                   # triage.py, decide.py, letter.py, runner.py
│   ├── learning/                   # corrections.py, playbook.py, ripple.py
│   ├── eval/score.py               # deterministic scoring vs gold
│   └── email/send.py               # Resend / SMTP, approval-gated
├── voice/                          # Pipecat bot (separate process)
│   ├── bot.py                      # pipeline: transport → VAD → STT → Mubit LLM → TTS
│   └── tools.py                    # lookup_customer, get_transactions, log_complaint, end_call
├── web/                            # Next.js app
├── data/                           # synthetic only
│   ├── bank_kb/*.md                # Thistle Bank (fictional) policies
│   ├── customers.json · transactions.json
│   ├── cases/practice/*.json       # calls (scripts) + emails, for corrections and warm-up
│   ├── cases/heldout/*.json        # never recorded for training
│   ├── eval/gold_*.jsonl           # hand-written gold labels
│   └── corrections/seed.jsonl      # guardrail corrections
└── scripts/                        # generate_synthetic.py, warm_mubit.py, run_eval.py, reset_demo.py
```

**Reusable from Redline (`git show fb545f9:<path>`):** `app/llm/mubit_client.py`, `app/db.py`, `app/learning/corrections.py`, `app/learning/playbook.py`, `app/eval/score.py`, `app/pipeline/runner.py`, `app/pipeline/retrieve.py` (BM25), `scripts/warm_mubit.py`, `web/components/MubitPanel.tsx`, `web/components/ui.tsx`, `web/app/globals.css`. The later Redline features (ripple, averaged scoreboard, demo rail, word-level diffs) weren't committed. They're described in [docs/redline/README.md](docs/redline/README.md) §7 and need rebuilding.

---

## 7. Synthetic data

Fictional bank: **Thistle Bank** (Scottish retail bank). Fictional complaints team, policies and customers.

| Data | Contents |
|---|---|
| `bank_kb/` | Complaints handling policy (clocks, letter types, FOS wording), fee refund policy, distress & inconvenience payment guidance (fictional bands), vulnerable customer policy, card dispute and chargeback policy, scam (APP) reimbursement policy, service standards |
| Customers + transactions | ~30 synthetic customers with accounts, fees, card payments, transfers, contact history |
| Practice cases (~40) | Emails and call scripts across categories; used for live corrections and Mubit warm-up (`record=full` with playbook) |
| Held-out cases (~25) | Different customers, wording and products; **always `metadata`**; gold labels written before any run |
| Caller scripts (3) | Lines the presenter reads as the customer on stage (§9), with natural variation |

**Deliberate patterns (what the corrections teach):**
| Pattern | Base model likely does | Correct handling |
|---|---|---|
| Vulnerability mentioned in passing ("I was in hospital", "since my wife died") | Misses it or doesn't act | Flag vulnerability with the quote; apply the policy (e.g. full fee refund + D&I payment, a specialist team) |
| Card-payment dispute | 8-week clock | Payment-services clock: 15 business days |
| Fees the customer was clearly warned about | Upholds it to please the customer | Not upheld, explained kindly, FOS rights given |
| Scam victim asks "will I get it back?" | Reassures, or promises | No promise before investigation; explain the process and timeline |
| Resolved on the call | Writes a full final response | Summary resolution communication, with FOS rights |

As we learned on Redline, run the base model first and **write the corrections around what it actually gets wrong**, not what we assume.

**Metrics (fixed rules vs gold):** category accuracy · **vulnerability recall** · clock accuracy · outcome accuracy · redress within ±£5 · letter checklist pass rate (FOS rights, outcome stated, reasons, redress, deadline, apology where upheld) · voice turn latency p50/p95 · cost per complaint.

---

## 8. Features

### P0: golden path (must ship)
1. Email intake → triage → decide → letter, all through Mubit, strict JSON
2. Case view with edit + reason → **Teach**; playbook versions via `rule.induce`
3. Held-out set + gold labels + scoring; **Compare** (base vs playbook, averaged)
4. Mubit trace panel; `record=metadata` for base and held-out runs
5. **Live voice agent** (browser): Pipecat + Deepgram + Mubit + TTS, with tools, live captions, post-call triage
6. **Approve & send**: a real email to the presenter's inbox

### P1: makes it a winner
7. **Teach & ripple**: correction → rule → held-out cases that the rule touches re-run and animate as tracked changes
8. Live triage card during the call (vulnerability flag appears with its quote)
9. Twilio phone number for expo judges to call
10. Closed model vs small model panel (quality, latency, £ per complaint)
11. Deadline countdowns in the queue

### P2: nice to have
12. Real inbound email webhook · 13. Root-cause analytics (top complaint drivers) · 14. Fast-refresh demo ("policy changes Monday": one correction updates handling)

### Out of scope
Real customer data · real banking integrations · authentication · production telephony compliance (call recording consent, PCI) · fully automatic decisions without human approval.

---

## 9. Demo script (3 minutes, live)

### Before going on stage
1. API and voice service running **without** `--reload`; web app open; Mubit console open on **Try models** in a second tab.
2. Seed guardrail corrections loaded and the playbook built. Practice cases sent with the playbook so the triage/decide adapter has trained (`scripts/warm_mubit.py`; check Tasks → Adapters for **Passed**). Start the adapter once in Try models beforehand.
3. Held-out set run 3× base and 3× latest playbook (Compare tab ready).
4. Presenter's phone logged into the email inbox that "Approve & send" will deliver to.
5. Mic tested in the room; text-chat fallback and recorded video ready.

### On stage
| Time | Beat | On screen |
|---|---|---|
| 0:00–0:15 | **Problem.** "Banks handle huge volumes of regulated complaints. Miss a vulnerability or a deadline and it's a breach; inconsistent outcomes end up at the Ombudsman." | Title |
| 0:15–1:00 | **Live call.** Presenter, as the customer, calls Ava: *"I've been charged overdraft fees three times this month. I was in hospital and couldn't sort it."* Ava empathises, checks identity, pulls up the fees, logs the complaint and says an email will follow. Captions and the triage card fill in live. | Live call view + trace panel |
| 1:00–1:25 | **The draft.** The call ends; triage, decision and letter appear (all Mubit calls). Point out what's wrong, e.g. vulnerability not acted on, or only one fee refunded. | Case view |
| 1:25–1:55 | **Correct + Teach & ripple.** Flag vulnerability, refund all three fees plus the D&I payment, reason: *"Fees during a documented hospital stay are refunded in full, plus a distress payment."* Ripple: a **different customer's email**, never seen, re-triaged and re-decided correctly. Tracked changes animate. | Ripple overlay |
| 1:55–2:15 | **Approve & send.** The resolution email lands on the presenter's phone. Hold it up. | Phone |
| 2:15–2:40 | **Prove.** Compare: held-out complaints, base → playbook, averaged over 3 runs: vulnerability recall, clock accuracy, outcome accuracy, letter compliance. | Compare |
| 2:40–2:55 | **Model update.** Mubit Try models: the case-decision adapter vs the provider, side by side. "Those corrected cases trained a small model the bank owns." | Mubit console |
| 2:55–3:00 | **Money line.** "Without Mubit, the agent answers complaints. With Mubit, it learns how your bank resolves them." | Title |

**Judge Q&A to prepare:**
- *Why not a speech-to-speech model?* → It wouldn't go through Mubit, so there'd be no training examples. The cascade keeps every decision as a Mubit call and gives auditable transcripts.
- *Does the AI decide complaints?* → No. It drafts; a handler approves every outcome and every email. That's both Consumer Duty and our product.
- *Isn't this just a prompt?* → The playbook applies corrections immediately; Mubit then distils the corrected calls into a small task adapter (Try models). Every stage is a Mubit task.
- *Overfitting?* → The held-out complaints are different customers and wording, gold labels were written before any run, and held-out calls are never recorded for training (enforced in code). Numbers are averaged over 3 runs.
- *Real data / privacy?* → Synthetic only, and PII is redacted before any Mubit call anyway.

---

## 10. Build plan (ruthlessly prioritised)
It's Saturday evening and code freeze is **Sun 10:00**. In order:

| # | Task | Done when |
|---|---|---|
| 1 | Restore reusable Redline modules (`mubit_client`, db, corrections, playbook, score, trace panel) | One Mubit call logged with a request ID |
| 2 | Synthetic Thistle Bank KB, customers, transactions, 40 practice + 25 held-out cases, gold labels | `data/` complete |
| 3 | `triage`, `decide`, `letter` prompts + schemas, **then freeze them** | Email case drafted end to end |
| 4 | Base run on practice + held-out, look at real errors, write seed guardrail corrections | First scoreboard |
| 5 | Warm Mubit: practice cases with the playbook (≥40 varied calls per task) | Console: Training → Testing |
| 6 | Voice agent: Pipecat + Deepgram + Mubit + TTS in the browser, tools, captions → case | A full call creates a case |
| 7 | UI: live call view, case view + Teach, learning, compare | Golden path clickable |
| 8 | Approve & send email; Teach & ripple | Email lands on a phone |
| 9 | Twilio number (expo), polish, backup video, rehearse | **Before Sun 10:00** |

**Risk register:** voice latency (mitigation: small model, short prompts, streaming, measure early) · venue Wi-Fi (tethering, video) · STT mishearing names and amounts (the agent confirms amounts back) · adapter not trained in time (start warm-up by midnight, show the playbook effect regardless) · prompt edits resetting tasks (freeze by step 3).

---

## 11. Setup

```powershell
# Backend (Python 3.11+)
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python -m uvicorn app.main:app --port 8000       # no --reload when demoing

# Voice service (separate terminal)
.\.venv\Scripts\python voice\bot.py                               # TODO(verify): Pipecat runner/transport flags

# Frontend (PowerShell)
cd web; npm install; npm run dev                                  # http://localhost:3000
```

`.env`:
```bash
# Mubit (all LLM calls)
MUBIT_BASE_URL=https://api.mubit.ai/openai/v1
MUBIT_API_KEY=mbt_...
MUBIT_MODEL=gpt-6-luna            # case tasks: triage, decide, letter, induce (one model, fixed)
VOICE_MODEL=gpt-4.1-mini          # voice turns: fast model (measure first-token latency via Mubit)

# Speech
DEEPGRAM_API_KEY=...
CARTESIA_API_KEY=...              # or ELEVENLABS_API_KEY
TTS_VOICE_ID=...                  # a British voice

# Email out
RESEND_API_KEY=...                # or SMTP_HOST / SMTP_USER / SMTP_PASSWORD
EMAIL_FROM=complaints@your-verified-domain
DEMO_INBOX=presenter@example.com

# Telephony (expo only)
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=...
```
Never put provider keys (OpenAI or Anthropic) in this app. Provider keys live in the Mubit console under **Provider keys**; the app sends only the Mubit key.

---

## 12. Ethics and data
- 100% synthetic customers, bank, accounts and complaints. No real data in prompts, the demo or screenshots.
- PII redaction before every Mubit call, even on synthetic data.
- Human in the loop: the AI drafts and flags, and a handler approves every outcome and every email.
- The voice agent says it's an AI assistant at the start of every call.
