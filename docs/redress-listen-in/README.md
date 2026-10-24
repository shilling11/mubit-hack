# Redress: bank complaints that resolve better with every correction

> **Night Shift: $65K Mubit Hackathon, London** · 23–25 October 2026 · <https://luma.com/nightshift-london>
>
> **One-liner:** Customers complain to their bank by phone or by email. On calls, Redress **listens in** silently, flags the few things the employee must not miss, and fills in the whole case when the call ends. For emails, Redress **reads the complaint and drafts the reply and the solution**. A human approves everything. Every model call goes through Mubit, and every correction becomes a rule immediately and a Mubit model update over time, so the next complaint, on either channel, is handled right first time.
>
> This replaces our first idea, **Redline** (RFP responses). Its full README, with everything we measured, is in [docs/redline/README.md](docs/redline/README.md), and its code is in commit `fb545f9`. **§3 below is the Mubit knowledge we learned building it. Read it before touching any model call.**

---

## 0. How to use this README (for teammates and coding agents)

- Build in the order in [§10 Build plan](#10-build-plan-ruthlessly-prioritised). The **email channel** comes first, because it carries the core loop and is the lowest risk. The **call channel** reuses the same pipeline and adds live transcription.
- **Hard rule: every LLM call goes through `app/llm/mubit_client.py`** (the Mubit gateway). Speech-to-text isn't an LLM task and calls Deepgram directly.
- **Freeze system prompts and JSON schemas early.** Mubit identifies a task by its system prompt, model, tools and output format. Changing any of them starts a new task with zero training examples (§3.4).
- Anything marked `TODO(verify)` hasn't been tested by us yet. Don't invent API details for Mubit, LiveKit, Deepgram, Gmail or Resend. Check their docs.
- All customers, banks, accounts and complaints are **synthetic**. No real customer data, ever: Mubit records request and reply content by default.

---

## 1. Problem overview and narrative

### The problem
UK banks handle very large volumes of complaints, by phone and by email: unexpected fees, card disputes, scams, mortgage errors, poor service. Every complaint is regulated. The FCA's complaint rules (DISP) set the clock and the content:

| Rule (FCA DISP, summarised: verify before quoting) | What it means operationally |
|---|---|
| A **prompt written acknowledgement** | Every complaint gets one, by email or letter |
| Resolved by the end of the **third business day** after receipt | A short "summary resolution communication" can close it, and must tell the customer about the Financial Ombudsman Service (FOS) |
| Otherwise a **final response within 8 weeks** | Must say whether the complaint is upheld, explain why, set out any redress, and give FOS referral rights (6 months) |
| **Payment services** complaints (card payments, transfers, direct debits) | Shorter clock: **15 business days**, up to 35 in exceptional cases |
| Fair treatment, Consumer Duty, vulnerable customers | Vulnerability must be spotted and acted on; outcomes must be consistent |

Each case is the **same recurring task**, whatever the channel:

> *Understand what happened → classify it and start the right clock → spot vulnerability → decide uphold / partial / reject under policy → calculate redress → write a compliant, human response.*

Where it goes wrong today:

| Failure | Cost |
|---|---|
| Vulnerability missed ("I was in hospital", "my husband just died") | Unfair outcome, regulatory breach, reputational damage |
| Wrong clock (a card-payment dispute treated as 8 weeks, not 15 business days) | Missed deadline, automatic breach |
| Inconsistent redress: two handlers, two answers | Unfair treatment; the customer goes to the Ombudsman, and the bank pays a case fee |
| After-call and inbox work: notes, logging, letters, replies | Most of a handler's time goes on paperwork, not customers |
| Promises made on the phone ("you'll definitely get it back") | A commitment the bank then has to honour or unwind |
| Generic AI chatbots and email auto-replies | Fluent but inconsistent; they promise what policy doesn't allow, or hedge on clear-cut cases |

### The insight
Complaints handlers already **correct** cases all day, and those corrections are the bank's real policy in practice:

- "Fees charged while the customer was in hospital are refunded in full, plus a distress-and-inconvenience payment."
- "Card-payment disputes are payment-services complaints: 15 business days, not 8 weeks."
- "Never tell a scam victim the money will definitely come back before the investigation."

Today those corrections stay in one handler's head, or a QA spreadsheet, and the knowledge doesn't move between the phone team and the email team.

### The solution
**Redress** works alongside the people already handling complaints:

| Channel | Who talks to the customer | What Redress does |
|---|---|---|
| **Phone** | The bank employee, as today | Listens silently and transcribes both sides. Shows **at most one nudge at a time**, only at the moments that matter (vulnerability heard, "this is a complaint", "don't promise an outcome", "confirm the callback time"). When the call ends, it **pre-fills the case**: summary, category, clock, vulnerability, commitments made, draft decision and the follow-up email |
| **Email** | Redress drafts; the handler sends | Reads the complaint (and the thread), triages it, drafts the acknowledgement immediately, then the decision and the resolution email. The handler edits and approves |

Both channels feed **one shared case pipeline**, so a correction made on a phone case also improves email handling, and the reverse. Each correction:
1. **immediately** becomes a playbook rule that the next case's calls include, and
2. **over time** becomes a Mubit task adapter: the corrected calls are Mubit's training examples, so a small, fast model learns the bank's complaint judgement.

### Why listen-in, not an AI that talks
- **Least overhead:** the employee does nothing new during the call. The paperwork after it, where the time actually goes, is done for them.
- **Safer:** a complaint outcome usually needs investigation, so nothing is decided live and the AI never speaks to a distressed customer.
- **Better for Mubit:** no speech synthesis and no sub-second turn deadline. Nudges can take 2–4s, which suits Mubit's measured latency. The employee confirming the wrap-up *is* the correction, so training data comes from normal work.

### Narrative for the judges (30 seconds)
> "A Thistle Bank customer rings, upset about overdraft fees, and mentions in passing they were in hospital. The employee handles the call; Redress listens and flags the vulnerability with the exact quote. When they hang up, the case is already written: category, deadline, decision and the follow-up email. The handler corrects one thing, and seconds later a different customer's **email** complaint is handled correctly first time. Those corrections train a small Mubit adapter, so this judgement runs on a model the bank owns."

**Money line:** *Without Mubit, the AI does the paperwork. With Mubit, it learns how your bank resolves complaints.*

---

## 2. Hackathon info

| Item | Detail |
|---|---|
| Event | Night Shift: $65K Mubit Hackathon in London |
| Format | 42-hour overnight hackathon, around 500 builders |
| Dates | Fri 23 Oct 2026, 17:00 → Sun 25 Oct 2026, 14:00 (clocks go back on Sunday) |
| Prizes | 1st $15,000 · 2nd $10,000 · 3rd $5,000 · $35,000 AI credits · $1.5M Mubit credits |

**Brief:** build a product that routes its LLM calls through Mubit (one base-URL change) and turns corrections into model updates for a recurring task.

**Tracks (top 3 judged across all):**
1. **Recurring tasks** ← primary.
2. **Own your intelligence layer** (closed model vs task-adapted open model: quality, cost, latency). `call.nudge` runs every ~20s of every call, so it's the highest-volume task and the clearest cost story for a small adapter.
3. **Fast refresh** (keeping pace with change): a policy change ("new fee-refund rule from Monday") taught with one correction.

| Judging criterion (equal weight) | How Redress scores |
|---|---|
| **Use of Mubit**: a correction becoming a model update | Live correction → rule → unseen complaint on the *other* channel handled right; corrected calls → Mubit adapter, shown in Try models. Every call visibly routed through Mubit |
| **Usefulness**: a real recurring task | Bank complaints: regulated, high-volume, costly when wrong, and most handler time goes on paperwork |
| **Technical execution** | Live dual-channel transcription, structured outputs, held-out set with hand-written gold labels, fixed-rule scoring, averaged runs |
| **Demo** | A live role-played call plus a real email arriving on a phone, in 3 minutes (§9) |

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
- If a task uses tools, the **tool definitions** are part of the fingerprint. Keep the tool list fixed.
- **Our two models:** `call.nudge` on a fast model and the case tasks on one other model. That's deliberate, and each stays fixed.

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
- **Latency (measured through Mubit, JSON output):** `gpt-6-luna` about 3–4s p50 per call; `gpt-4o-mini` and `gpt-4.1-mini` about 1.4s. Fine for nudges (non-blocking) and post-call drafting; too slow for an AI that talks in real time, which is one reason we listen in instead (§1).
- **Ops gotchas:** `uvicorn --reload` restarts kill in-flight background work, so demo without `--reload`. npm was broken under Git Bash on our Windows machine but works in PowerShell. Next.js versions before 16.4.1 had critical advisories, so we use 16.4.3.

---

## 4. Product overview

### 4.1 Channels

**Phone: listen-in assistant**
1. The customer calls; the bank employee answers as normal. Redress joins as a **silent participant**: it records and transcribes both sides on separate audio tracks, so "who said what" is exact.
2. The live transcript appears in a slim side panel. **Nudges** appear only when needed, at most one at a time; they expire on their own and can be dismissed in one click:

   | Nudge | Fires when | Example |
   |---|---|---|
   | `vulnerability` | Health, bereavement, money worries, confusion, distress | *"Customer mentioned a hospital stay → offer specialist support."* (with the quote) |
   | `complaint` | Dissatisfaction is expressed: it's a complaint even if the word isn't used | *"This is a complaint: it's been logged and the clock has started."* |
   | `no_promise` | The employee promises an outcome before investigation | *"Avoid promising a refund: explain what happens next."* |
   | `expectation` | The customer asks "when", or the call is ending | *"Confirm when they'll hear back and how."* |
   | `info_needed` | A fact the case needs is missing | *"Ask for the date of the first fee."* |
3. When the call ends, the case is **pre-filled within seconds**: summary, category, regulatory clock, vulnerability flags (with quotes), commitments the employee made ("I'll call you Friday"), draft decision and redress, and the follow-up email. The employee confirms or edits. **That edit is the correction.**

**Email: drafting assistant**
1. A complaint email arrives in the bank's complaints inbox (seeded for the demo, or a real mailbox via IMAP).
2. Redress triages it straight away and drafts the **acknowledgement** (one click to send).
3. It then drafts the **decision and resolution email**: a summary resolution communication if it can be resolved within three business days, a final response otherwise, or an **info request** if a fact is missing. Follow-ups in the same thread join the same case.
4. The handler edits and clicks **Approve & send**. Edits are corrections.

### 4.2 One shared case pipeline (every LLM step is a Mubit task)
| # | Mubit task | Channel | Input (user message) | Output (strict JSON) | Volume · corrected by |
|---|---|---|---|---|---|
| 1 | `call.nudge` | Phone (live) | Last ~90s of transcript + nudges already shown + case so far + playbook | 0–2 nudges: type, message (≤ 15 words), quote, priority | **Highest:** every ~20s of every call · dismissals with a reason |
| 2 | `complaint.triage` | **Both** | Final transcript **or** email thread + customer profile + playbook | Category, product, clock type, **vulnerability [type, quote]**, severity, customer's ask, summary, commitments made, missing info | Every case · **core** |
| 3 | `complaint.decide` | Both | Triage + transactions + policy passages + playbook | Outcome (upheld / partially / not upheld / need info), reasons, **redress lines**, confidence | Every case · **core** |
| 4 | `complaint.reply` | Both | Case + decision + reply type (acknowledgement / info request / summary resolution / final response) + thread or call commitments + playbook | Subject, body, required-elements checklist | Every case · email edits |
| 5 | `rule.induce` | – | Correction + the handler's reason | One general rule + when it applies + keywords | Every correction |

Because triage, decide and reply are **one task each for both channels**, phone and email cases train the same three adapters. That gives twice the examples, and corrections carry across channels.

**Plain code, no LLM:** speaker separation (separate tracks), nudge rate-limiting (one visible at a time, a cooldown per type, no repeats), clock and deadline arithmetic, PII redaction, policy retrieval (BM25), email threading, the reply compliance checklist, and scoring.

### 4.3 Where corrections come from (no extra work for the employee)
| Signal | Becomes |
|---|---|
| Edits to the pre-filled wrap-up (category, clock, vulnerability, commitments) | A triage correction → rule |
| Edits to the decision or redress | A decision correction → rule |
| Edits to the email (word-level diff) | A reply correction → rule |
| A nudge dismissed with a one-click reason ("not vulnerability", "already done") | A nudge correction. Repeated dismissals become a rule |
| Approve with no edits | Recorded as a confirmation (no rule) |

Each correction can carry an **optional reason** from a dropdown or a short note, so there's no essay-writing. `rule.induce` turns the reason and the diff into a general rule.

### 4.4 Handler workspace (web app)
- **Live call:** two-lane transcript (customer / employee), the current nudge, and the case so far.
- **Inbox:** email complaints with deadline countdowns and acknowledgement status.
- **Case view:** triage, decision and redress, draft email, evidence (transcript lines, transactions, policy passages). Edit anything, give a reason → **Teach** or **Teach & ripple**. **Approve & send** sends the real email.
- **Learning:** corrections as tracked changes, playbook versions, induced rules.
- **Compare:** held-out cases from both channels, base vs playbook, averaged over 3 runs.
- **Mubit trace panel:** every call with task, request ID, model, latency and record mode.

---

## 5. Architecture and technologies

### 5.1 Diagram
```text
 PHONE                                                   EMAIL
 Customer ──audio──┐                                      Customer ──email──► complaints inbox
                   ▼                                                            │ IMAP poll (or webhook)
          ┌──────────────── call room (LiveKit, WebRTC) ────────────────┐       │
          │ customer track         employee track                       │       │
          │        └── Redress listener (silent participant) ──┐        │       │
          └────────────────────────────────────────────────────┼────────┘       │
                  per-track streaming STT (Deepgram) ◄─────────┘                │
                         │ transcript segments, speaker known                    │
                         ▼                                                       ▼
 ┌──────────────────────────────────── Redress API (FastAPI) ─────────────────────────────────────┐
 │ live: transcript store → nudge loop (call.nudge, debounced) → WebSocket to the UI              │
 │ cases: intake (call end / new email) → redaction → triage → decide → reply                     │
 │ learning: corrections → rule.induce → playbook vN · ripple · scoring · SQLite                  │
 │ app/llm/mubit_client.py ──────────────────────────► Mubit gateway ──► provider model           │
 │ email out: SMTP (Gmail app password) or Resend, only after the handler approves                │
 └────────────────────────────────────────────────────────────────────────────────────────────────┘
                         ▲ REST + WebSocket
           ┌─────────────┴──────── Web app (Next.js 16 + Tailwind 4) ────────┐
           │ live call · inbox · case view · learning · compare · traces     │
           └─────────────────────────────────────────────────────────────────┘
```

### 5.2 Stack
| Layer | Choice | Notes |
|---|---|---|
| Call room | **LiveKit** (Cloud free tier or self-hosted), WebRTC | The customer and employee join from browsers or phones; the listener joins as a hidden, muted participant and subscribes to each track. Alternative: Daily + Pipecat. `TODO(verify)`: LiveKit Agents API for a non-publishing participant |
| Speech-to-text | **Deepgram** streaming (Nova family), one stream per track | Interim results for captions, endpointing to detect "utterance finished", punctuation. Alternative: AssemblyAI streaming |
| Email in | **Gmail inbox via IMAP polling** (app password), every ~10s | Simplest real inbound with no webhooks. Alternatives: Postmark or Resend inbound webhooks `TODO(verify)` |
| Email out | **SMTP** on the same Gmail account, or **Resend** | Real email to a phone on stage. Human approval required |
| LLM gateway | **Mubit**, OpenAI SDK, one base URL | One fixed model per task (§3.4): fast model for `call.nudge`, one model for the case tasks |
| Backend | Python 3.11, FastAPI, Pydantic, SQLite, rank-bm25, asyncio | Reuse Redline modules (§6) |
| Frontend | Next.js 16.4.3, React 19, Tailwind 4, lucide-react | Reuse Redline's trace panel, UI kit and diff view |
| Telephony (stretch) | Twilio number + Media Streams (both call legs) | So expo judges can ring in from a real phone |

### 5.3 Design decisions
- **Separate tracks, not diarisation.** Transcribing each participant's audio on its own stream gives exact speaker labels and avoids diarisation errors, which matters when the nudge is "*the employee* just promised a refund".
- **Nudge loop:** trigger `call.nudge` when a speaker finishes an utterance, debounced to at most one request in flight and at least ~15s apart. Send a window of recent transcript, not the whole call, so inputs stay short and varied. Nudges never block the call and expire after ~20s. The rate limits, cooldowns and dedupe are plain code.
- **Post-call wrap-up:** on hang-up, run `complaint.triage` on the full transcript, then `decide`, then `reply` (a follow-up email confirming what was agreed). Target: case ready within ~10s.
- **Email threading** uses `Message-ID` / `In-Reply-To`, so replies attach to the open case. The acknowledgement is drafted the moment an email lands; an "auto-send acknowledgements" toggle is available.
- **Latency is fine:** nothing waits on the model in real time. Nudges taking 2–4s through Mubit is acceptable, unlike an AI that talks.
- **PII:** Mubit stores content by default. Data is synthetic, but we still redact card numbers, sort codes, account numbers and dates of birth by regex before any Mubit call.
- **Consent:** standard "calls may be recorded" notice; Redress assists the employee and never speaks to the customer.
- **Fallbacks:** (1) a pre-recorded two-track call replayed through the same STT path; (2) a transcript simulator (timed text lines); (3) seeded emails; (4) a recorded video.

### 5.4 Regulatory clock (plain code, from triage output)
| Situation | Clock | Deadline |
|---|---|---|
| Resolved by the end of the 3rd business day | Summary resolution | Day 3 (business days) |
| Payment services (card payment, transfer, direct debit) | PSR | 15 business days (35 exceptional) |
| Everything else | DISP final response | 8 weeks |

UK bank holidays in the business-day calculation: `TODO(verify)`.

---

## 6. Repo layout (planned)
```text
mubit-hack/
├── README.md                       # this file
├── docs/redline/README.md          # previous idea: full context + measured results
├── .env.example · requirements.txt
├── app/                            # FastAPI
│   ├── main.py                     # REST + WebSocket (live transcript, nudges, case updates)
│   ├── config.py · db.py · models.py
│   ├── llm/
│   │   ├── mubit_client.py         # ONLY model gateway (reuse from fb545f9)
│   │   └── prompts/                # nudge, triage, decide, reply, induce_rule (frozen early)
│   ├── cases/                      # intake, redaction, deadlines, policy retrieval
│   ├── calls/                      # transcript store, nudge loop, wrap-up trigger
│   ├── email/                      # imap_poll.py, threading.py, send.py (approval-gated)
│   ├── pipeline/                   # triage.py, decide.py, reply.py, runner.py
│   ├── learning/                   # corrections.py, playbook.py, ripple.py
│   └── eval/score.py               # deterministic scoring vs gold
├── listener/                       # LiveKit silent participant (separate process)
│   └── agent.py                    # subscribe to tracks → Deepgram → POST segments to the API
├── web/                            # Next.js app
├── data/                           # synthetic only
│   ├── bank_kb/*.md                # Thistle Bank (fictional) policies
│   ├── customers.json · transactions.json
│   ├── cases/practice/             # call scripts (two speakers) + email threads
│   ├── cases/heldout/              # never recorded for training
│   ├── audio/                      # pre-recorded two-track demo call (fallback)
│   ├── eval/gold_*.jsonl           # hand-written gold labels
│   └── corrections/seed.jsonl      # guardrail corrections
└── scripts/                        # generate_synthetic.py, warm_mubit.py, run_eval.py, replay_call.py, reset_demo.py
```

**Reusable from Redline (`git show fb545f9:<path>`):** `app/llm/mubit_client.py`, `app/db.py`, `app/learning/corrections.py`, `app/learning/playbook.py`, `app/eval/score.py`, `app/pipeline/runner.py`, `app/pipeline/retrieve.py` (BM25), `scripts/warm_mubit.py`, `web/components/MubitPanel.tsx`, `web/components/ui.tsx`, `web/app/globals.css`. The later Redline features (ripple, averaged scoreboard, demo rail, word-level diffs) weren't committed. They're described in [docs/redline/README.md](docs/redline/README.md) §7 and need rebuilding.

---

## 7. Synthetic data

Fictional bank: **Thistle Bank** (Scottish retail bank). Fictional complaints team, policies and customers.

| Data | Contents |
|---|---|
| `bank_kb/` | Complaints handling policy (clocks, letter types, FOS wording, acknowledgement), fee refund policy, distress & inconvenience payment guidance (fictional bands), vulnerable customer policy, card dispute policy, scam (APP) reimbursement policy, call-handling standards (no promises, expectations) |
| Customers + transactions | ~30 synthetic customers with accounts, fees, card payments, transfers, contact history |
| Practice cases (~45) | ~15 two-speaker call scripts + ~30 email threads, across categories; used for live corrections and Mubit warm-up (`record=full` with playbook) |
| Held-out cases (~25) | ~8 calls + ~17 emails, different customers and wording; **always `metadata`**; gold labels written before any run |
| Demo call script | The lines the two presenters role-play on stage (§9), plus a pre-recorded two-track version |

**Deliberate patterns (what the corrections teach):**
| Pattern | Base model likely does | Correct handling |
|---|---|---|
| Vulnerability mentioned in passing | Misses it or doesn't act | Nudge with the quote; flag it; apply the policy (full fee refund + D&I payment, specialist team) |
| Card-payment dispute | 8-week clock | Payment-services clock: 15 business days |
| Employee says "you'll get that back" | Nothing | `no_promise` nudge; the wrap-up records it as a commitment to honour or correct |
| Fees the customer was clearly warned about | Upholds it to please the customer | Not upheld, explained kindly, FOS rights given |
| Scam victim asks "will I get it back?" (email) | Reassures, or promises | No promise before investigation; explain the process and timeline |
| Email missing a key fact | Guesses | Info request reply |
| Resolved on the call | Drafts a full final response | Summary resolution communication, with FOS rights |

As we learned on Redline, **run the base model first and write the corrections around what it actually gets wrong**, not what we assume.

**Metrics (fixed rules vs gold):** nudge precision and recall by type (within a time window of the gold line) · category accuracy · **vulnerability recall** · clock accuracy · outcome accuracy · redress within ±£5 · reply checklist pass rate (FOS rights, outcome, reasons, redress, deadline, apology where upheld) · time from hang-up to case ready · cost per complaint.

---

## 8. Features

### P0: golden path (must ship)
1. **Email channel:** seeded inbox + IMAP → triage → decide → reply (acknowledgement and resolution), all through Mubit, strict JSON
2. Case view: edit + reason → **Teach**; playbook versions via `rule.induce`
3. Held-out set (both channels) + gold labels + scoring; **Compare** (base vs playbook, averaged)
4. Mubit trace panel; `record=metadata` for base and held-out runs, enforced in code
5. **Call channel:** LiveKit room + silent listener + Deepgram per track → live two-lane transcript → post-call wrap-up into a case
6. **Approve & send**: a real email to the presenter's inbox

### P1: makes it a winner
7. **Live nudges** (`call.nudge`) with one-click dismiss + reason
8. **Teach & ripple across channels:** a correction on a call case re-runs the held-out *email* cases it touches, animated as tracked changes
9. Closed model vs small model panel for `call.nudge` (quality, latency, £ per call)
10. Deadline countdowns; auto-send acknowledgements toggle
11. Expo mode: judges email the demo complaints address and watch the draft appear

### P2: nice to have
12. Twilio phone number (judges ring in from a real phone) · 13. Root-cause analytics (top complaint drivers) · 14. Fast-refresh demo ("policy changes Monday") · 15. An AI voice that talks to customers (stretch only: the riskiest part, and it needs sub-second latency)

### Out of scope
Real customer data · real banking or CRM integrations · authentication · production telephony compliance · automatic decisions or emails without human approval.

---

## 9. Demo script (3 minutes, live)

Two presenters: **A** plays the Thistle Bank employee (drives the laptop), **B** plays the customer (joins the call from a phone or a second laptop).

### Before going on stage
1. API and listener running **without** `--reload`; web app open; Mubit console open on **Try models** in a second tab.
2. Seed guardrail corrections loaded and the playbook built. Practice cases from both channels sent with the playbook, so the triage/decide adapters have trained (`scripts/warm_mubit.py`; check Tasks → Adapters for **Passed**). Start the adapter once in Try models beforehand.
3. Held-out set run 3× base and 3× latest playbook (Compare tab ready).
4. A's phone logged into the inbox that **Approve & send** delivers to.
5. Call room tested in the venue (mics, Wi-Fi or tethering); `scripts/replay_call.py` and the recorded video ready as fallbacks.

### On stage
| Time | Beat | On screen |
|---|---|---|
| 0:00–0:15 | **Problem.** "Banks handle huge volumes of regulated complaints. Most handler time goes on paperwork, and one missed vulnerability or deadline is a breach." | Title |
| 0:15–1:00 | **Live call.** B: *"I've been charged overdraft fees three times this month. I was in hospital and couldn't sort it."* The two-lane transcript streams. A **vulnerability nudge** appears with the quote. A slips: *"Don't worry, we'll refund those."* A **no-promise nudge** appears. A recovers and sets expectations. | Live call panel + trace panel |
| 1:00–1:20 | **Hang up → case ready.** Within seconds: summary, category, clock, vulnerability, commitments, draft decision and follow-up email, all Mubit calls. Point out what the base draft got wrong (e.g. only one fee refunded, no D&I payment). | Case view |
| 1:20–1:50 | **Correct + Teach & ripple.** Refund all three fees plus the D&I payment, with reason: *"Fees during a documented hospital stay are refunded in full, plus a distress payment."* The ripple re-runs held-out **email** complaints from other customers that the rule touches: corrected in tracked changes. "Taught on a phone call, applied to the inbox." | Ripple overlay |
| 1:50–2:10 | **Approve & send.** The resolution email lands on A's phone. Hold it up. | Phone |
| 2:10–2:35 | **Prove.** Compare: held-out cases, both channels, base → playbook, averaged over 3 runs: vulnerability recall, clock accuracy, outcome accuracy, reply compliance. | Compare |
| 2:35–2:52 | **Model update.** Mubit Try models: the decision adapter vs the provider, side by side. "Those corrected cases trained a small model the bank owns." | Mubit console |
| 2:52–3:00 | **Money line.** "Without Mubit, the AI does the paperwork. With Mubit, it learns how your bank resolves complaints." | Title |

**Judge Q&A to prepare:**
- *Why doesn't the AI talk to the customer?* → Complaint outcomes need investigation and a human decision. Listening in removes the paperwork without putting an AI in front of a distressed customer, and it adds no latency or risk to the call.
- *Isn't the employee distracted by nudges?* → At most one at a time, only for five high-stakes moments, with expiry and one-click dismiss. Dismissals are training signal.
- *Isn't this just a prompt?* → The playbook applies corrections immediately; Mubit then distils the corrected calls into small task adapters (Try models). Every stage is a Mubit task, and phone and email share them.
- *Overfitting?* → Held-out cases are different customers and wording on both channels, gold labels were written before any run, and held-out calls are never recorded for training (enforced in code). Numbers are averaged over 3 runs.
- *Real data / privacy?* → Synthetic only, and PII is redacted before any Mubit call anyway.

---

## 10. Build plan (ruthlessly prioritised)
It's Saturday evening and code freeze is **Sun 10:00**. In order:

| # | Task | Done when |
|---|---|---|
| 1 | Restore reusable Redline modules (`mubit_client`, db, corrections, playbook, score, trace panel) | One Mubit call logged with a request ID |
| 2 | Synthetic Thistle Bank KB, customers, transactions, practice + held-out calls and emails, gold labels | `data/` complete |
| 3 | `triage`, `decide`, `reply` (and `nudge`) prompts + schemas, **then freeze them** | An email case drafted end to end |
| 4 | Base run on practice + held-out, look at the real errors, write seed guardrail corrections | First scoreboard |
| 5 | Warm Mubit: practice cases from both channels with the playbook (≥40 varied calls per task) | Console: Training → Testing |
| 6 | Email: IMAP poll + threading + Approve & send | A real email in, a real reply out |
| 7 | Call: LiveKit room + listener + Deepgram per track → transcript → wrap-up case | A full role-played call creates a case |
| 8 | UI: live call panel, inbox, case view + Teach, learning, compare | Golden path clickable |
| 9 | Nudges; Teach & ripple across channels | Nudge appears on the hospital line; ripple fixes an email case |
| 10 | Polish, replay fallback, backup video, rehearse | **Before Sun 10:00** |

**Risk register:** venue audio and Wi-Fi (tethering, replay script, video) · STT mishearing amounts (the wrap-up shows the transcript line next to every figure) · nudge noise (strict rate limits; tune on practice calls) · adapter not trained in time (start warm-up by midnight; show the playbook effect regardless) · prompt edits resetting tasks (freeze by step 3) · Gmail blocking IMAP/SMTP (use an app password; Resend as backup).

---

## 11. Setup

```powershell
# Backend (Python 3.11+)
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python -m uvicorn app.main:app --port 8000          # no --reload when demoing

# Call listener (separate terminal)
.\.venv\Scripts\python listener\agent.py                             # TODO(verify): LiveKit Agents run command

# Frontend (PowerShell)
cd web; npm install; npm run dev                                     # http://localhost:3000

# Fallback: replay a recorded two-track call through the same pipeline
.\.venv\Scripts\python -m scripts.replay_call data\audio\demo_call
```

`.env`:
```bash
# Mubit (all LLM calls)
MUBIT_BASE_URL=https://api.mubit.ai/openai/v1
MUBIT_API_KEY=mbt_...
MUBIT_MODEL=gpt-6-luna            # case tasks: triage, decide, reply, induce (one model, fixed)
NUDGE_MODEL=gpt-4.1-mini          # live nudges: fast model (one model, fixed)

# Call room + speech
LIVEKIT_URL=wss://...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
DEEPGRAM_API_KEY=...

# Email (simplest: one Gmail account with 2FA + an app password)
GMAIL_ADDRESS=thistle.complaints.demo@gmail.com
GMAIL_APP_PASSWORD=...
IMAP_POLL_SECONDS=10
# or: RESEND_API_KEY=... and EMAIL_FROM=complaints@your-verified-domain
DEMO_INBOX=presenter@example.com   # where Approve & send delivers on stage

# Telephony (stretch)
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=...
```
Never put provider keys (OpenAI or Anthropic) in this app. Provider keys live in the Mubit console under **Provider keys**; the app sends only the Mubit key.

---

## 12. Ethics and data
- 100% synthetic customers, bank, accounts and complaints. No real data in prompts, the demo or screenshots.
- PII redaction before every Mubit call, even on synthetic data.
- Human in the loop: Redress drafts and flags; a person handles the call, approves every outcome and sends every email.
- Recording consent: standard "calls may be recorded" notice. The privacy notice says AI assists the complaints team.
