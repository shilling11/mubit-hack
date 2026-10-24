# Redress: QA on every regulated call, with a model that learns from your analysts

> **Night Shift: $65K Mubit Hackathon, London** · 23–25 October 2026 · <https://luma.com/nightshift-london>
>
> **One-liner:** Bank call QA checks **1–2% of calls** by hand. Redress reviews **100%** of a bank's calls against its scorecard and the FCA's rules. It sends the risky ones to a QA analyst, and turns every correction the analyst makes into a rule straight away and a Mubit model update over time. Built for **outsourced QA firms**: one model per bank client, trained only on that client's labels.
>
> **Direction change (Sat 22:30, Abdul).** This README now describes **v3**.
> - Sultan's listen-in + email version (20:46) is kept **unchanged** at [docs/redress-listen-in/README.md](docs/redress-listen-in/README.md). Its Deepgram, Gmail IMAP/SMTP, redaction and Mubit parts carry straight over.
> - The first idea, Redline, is at [docs/redline/README.md](docs/redline/README.md).
> - **§3 (Mubit knowledge) is unchanged. Read it before touching any model call.**
>
> **Read next:**
> - [docs/QA_RESEARCH.md](docs/QA_RESEARCH.md): how call QA really works, with sources
> - [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): flow, Mubit tasks, data model, **routes v3**
> - [docs/CALLING.md](docs/CALLING.md): the call recording path (Sultan)
> - [docs/planning/](docs/planning/): decision notes and the risk log

---

## 0. How to use this README (for teammates and coding agents)

- Build in the order in [§10](#10-build-plan). The **review task on imported transcripts** comes first: it's the core loop and the lowest risk. The call recording path feeds the same pipeline.
- **Hard rule: every LLM call goes through `app/llm/mubit_client.py`** (the Mubit gateway). Speech-to-text isn't an LLM task and calls Deepgram directly.
- **Freeze system prompts and JSON schemas by 00:00.** Mubit identifies a task by its system prompt, model, tools and output format. Changing any of them starts a new task with zero training examples (§3.4). Each client's scorecard lives **in its system prompt**, which is how each bank gets its own model.
- **Held-out calls are `x-middleware-record: metadata`, set in code.**
- Anything marked `TODO(verify)` hasn't been tested by us yet. Don't invent API details for Mubit, Deepgram or Gmail. Check their docs.
- Everything is **synthetic**: the QA firm, the banks, the agents and the customers. Mubit records request and reply content by default.

---

## 1. Problem and narrative

### How call QA works today (sources in [docs/QA_RESEARCH.md](docs/QA_RESEARCH.md))
- Calls are recorded. **A random 1–2% are sampled** (ContactBabel survey of 200+ UK contact centres), and **an analyst listens to the whole call**: advice calls run about 90 minutes, and one audit took 24 minutes.
- Analysts score a **weighted scorecard with auto-fail items** and meet monthly to align their scoring. Findings become coaching, urgent escalations, and **reports that feed the bank's Consumer Duty board report**.
- QA can be **in-house or outsourced** (TCC Group, Huntswood, KPMG). The FCA only requires that the checkers are **independent** of the work they check (SYSC 6.1).
- **What analysts look for:**
  - missed **complaints**, even when the customer never uses the word;
  - missed **vulnerability** (health, bereavement, money worries, confusion);
  - **promises or misleading statements**;
  - **missing checks or disclosures**;
  - the **wrong deadline** (8 weeks, or 15 business days for payments).

### What's broken
| Problem | Cost |
|---|---|
| 98% of calls are never checked | Missed complaints and missed vulnerable customers stay hidden. The bank can't evidence Consumer Duty outcomes. |
| Analysts disagree with each other | "Reviews were at times inconsistent and uncoordinated" (Key Group) |
| Today's AI QA is **configured, not trained** | A rented big model you instruct ("write guidelines… tune it until it's calibrated"). When analysts disagree, someone rewrites the instructions. **The model never learns.** |

### The solution
**Redress** is the QA firm's workbench:
1. **Review 100%.** An AI reviewer scores every call against the client's scorecard, with the quote and timestamp for every answer.
2. **Route.** Critical failures are escalated now. High-risk and low-confidence calls go to an analyst. A random 1% audit keeps it honest. The rest is auto-accepted.
3. **Label.** The analyst sees the same evaluation form they use today, pre-filled. They ✓ agree, or change an answer and give a one-line reason.
4. **Learn.** Each override becomes a playbook rule (re-tested on last week's calls before it goes live) and a Mubit training example. **Agreement per scorecard item** rises; items above 95% stop needing a human.
5. **Report.** The weekly client report is written section by section by a second Mubit task. The analyst's edits teach that task too.

### Pitch points (agreed)
1. **Today's AI QA never learns.** "If the analysts disagree, someone rewrites the instructions. The model itself never learns." Redress is trained by the analysts, every day.
2. **100% coverage becomes affordable.** Running every long call through a big model costs real money. That's why Aveni built small models (they claim "up to 25× cheaper"), and it took them seven years. **Mubit builds a small model from the firm's own calls, with no ML team.**
3. **One model per bank client.** Each bank's scorecard is a separate Mubit task, so a separate model is trained **only on that bank's calls**. Nothing crosses between clients.
4. **Stable scores for auditors.** A rented model changes when the provider updates it. A Mubit model only changes when a new version passes Mubit's tests and you choose to switch.

**Closing line:** *"Today's AI QA is configured. Redress is trained, by your analysts, every day."*

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
1. **Recurring tasks** (primary): the same review after every call, corrected by analysts.
2. **Own your intelligence layer:** 100% coverage only pays on a small task model. The Compare tab shows quality, latency and cost per 1,000 calls side by side.
3. **Fast refresh:** a rule change (a new FCA rule, or a new client policy) taught with one correction and tested on the archive.

| Judging criterion (equal weight) | How Redress scores |
|---|---|
| **Use of Mubit**: a correction becoming a model update | Analyst override → rule → unseen calls scored right; corrected calls → `review.thistle` adapter version, shown in Try models; a second client's task shows one model per client |
| **Usefulness**: a real recurring task | Regulated call QA: 1–2% sampled today, analysts paid per review, FCA board reports depend on it |
| **Technical execution** | Speaker-separated transcription, strict JSON scorecards with evidence timestamps, risk routing, an agreement metric, a held-out set with gold labels, averaged runs |
| **Demo** | A live role-played call scored seconds after hang-up, a label → rule → retest, and a client report landing in Gmail, in 3 minutes (§9) |

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
- **Our model (v3):** one fixed model (`MUBIT_MODEL`) for every `review.*`, `report.*` and `rule.induce` task.

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
- **Latency (measured through Mubit, JSON output):** `gpt-6-luna` about 3–4s p50 per call; `gpt-4o-mini` and `gpt-4.1-mini` about 1.4s. Fine for post-call review, which runs after the call ends; too slow for an AI that talks in real time.
- **Ops gotchas:** `uvicorn --reload` restarts kill in-flight background work, so demo without `--reload`. npm was broken under Git Bash on our Windows machine but works in PowerShell. Next.js versions before 16.4.1 had critical advisories, so we use 16.4.3.

---

## 4. Product overview

### 4.1 Who uses it
| User | Where | What they do |
|---|---|---|
| **QA analyst** at Harbour Assurance (a fictional outsourced QA firm) | Queue → evaluation form | Confirms or overrides the AI's answers, with a reason |
| **QA lead** | Agreement · Learning · Report | Watches agreement per item, checks rules before they go live, edits and sends the client report |
| **Client complaints manager** at Thistle Bank | Their Gmail | Receives urgent escalations and the weekly report |

**Nothing leaves Harbour without a human click.** Escalations and reports are drafted, then sent by the analyst or lead.

### 4.2 The flow
**Ingest** (upload a recording or import transcripts) → **Review** (`review.<client>`, every call) → **Route** (escalate / analyst / audit / auto) → **Label** (the evaluation form) → **Learn** (rule, test on archive, agreement) → **Report** (`report.<client>`, section by section) → **Send** (Gmail).

Full detail, the Mubit task table, the data model and **routes v3** are in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

### 4.3 Mubit tasks
| Task | Per client? | What it does |
|---|---|---|
| `review.thistle`, `review.northwind` | **Yes**: the scorecard is in the system prompt | Scores one call: items + quote + timestamp + confidence, complaint, deadline, vulnerability, risk tier |
| `report.thistle` | **Yes**: the report template is in the system prompt | Writes one report section or finding (kept short, so it can be trained on) |
| `rule.induce` | Shared | Turns an override and its reason into a general rule |

### 4.4 Screens
Wall (100 tiles) · Queue · Evaluation form · Agreement · Report editor · Learning · Mubit panel. Details are in ARCHITECTURE §6. Visual style is owned by the UI session.

---

## 5. Architecture and technologies

| Layer | Choice | Notes |
|---|---|---|
| Recording | Browser `MediaRecorder` (laptop mic), or upload a file | No call room needed. Calls are reviewed after they end ([docs/CALLING.md](docs/CALLING.md)) |
| Speech-to-text | **Deepgram pre-recorded**, `diarize=true`, `utterances=true` | Speaker mapping in code, plus a Swap button. `TODO(verify)` the model name |
| LLM gateway | **Mubit**, OpenAI SDK, one base URL | One fixed model for all `review.*` / `report.*` tasks (`MUBIT_MODEL`) |
| Backend | Python 3.11, FastAPI, Pydantic, SQLite | Reuse Redline's `mubit_client`, db, corrections, playbook, score |
| Email out | **Gmail SMTP** (app password) | Escalations and client reports, after a human click |
| Frontend | Next.js 16.4.3, React 19, Tailwind 4 | Polls the API every 1–2 s; no WebSockets |

**PII:** card numbers, sort codes, account numbers, dates of birth and postcodes are redacted by regex before any Mubit call, even though the data is synthetic.

---

## 6. Repo layout (planned)
```text
mubit-hack/
├── README.md                     # this file (v3)
├── docs/
│   ├── QA_RESEARCH.md · ARCHITECTURE.md · CALLING.md
│   ├── planning/                 # decision notes, RISKS.md (Mubit risk log)
│   ├── redress-listen-in/        # Sultan's previous version, unchanged
│   └── redline/                  # first idea
├── app/                          # FastAPI
│   ├── main.py · config.py · db.py
│   ├── llm/mubit_client.py       # the ONLY model gateway (from fb545f9)
│   ├── llm/prompts/              # review_thistle.md, review_northwind.md, report_thistle.md, induce_rule.md (FROZEN 00:00)
│   ├── ingest/                   # deepgram.py, redact.py, import_calls.py
│   ├── review/                   # run.py, route.py, agreement.py
│   ├── learning/                 # corrections.py, playbook.py, test_archive.py
│   ├── report/                   # sections.py, send.py
│   └── eval/score.py             # gold vs output, averaged runs
├── web/                          # Next.js (UI session)
├── data/                         # synthetic only
│   ├── clients/*.json            # scorecards, report templates, policies
│   ├── calls/thistle_practice/*.json · calls/thistle_heldout/*.json · calls/northwind/*.json
│   ├── eval/gold_thistle.jsonl   # written BEFORE any run
│   └── audio/                    # demo recordings + fallback file
└── scripts/                      # generate_calls.py, warm_mubit.py, run_eval.py, reset_demo.py
```

---

## 7. Synthetic data
- **Harbour Assurance** (the QA firm) and its clients **Thistle Bank** and **Northwind Finance**, with fictional agents and customers.
- **Thistle: 100 call transcripts.**
  - **About 40% are hard cases**: a complaint never called a complaint, vulnerability mentioned in passing ("since my husband passed"), the wrong deadline given, a refund promised, a skipped identity check.
  - 75 practice calls · 25 held-out calls (`metadata`).
- **Gold labels for the held-out 25 are written before any run.**
- **Northwind:** 12–20 calls (its task stays partly trained on purpose).
- As Redline taught us, **run the base model first and write corrections around what it actually gets wrong.**

**Metrics** (fixed rules against gold labels):
- item accuracy
- **critical-fail recall**
- complaint recall
- vulnerability recall
- agreement %
- latency p50
- cost per 1,000 calls

---

## 8. Features
**P0 (must ship):**
1. Import transcripts → `review.thistle` (strict JSON, quotes + timestamps), all through Mubit
2. Routing + queue + **evaluation form** with override reasons → corrections → `rule.induce` → playbook vN
3. **Test on archive** (before → after) + **agreement per item**
4. **Record call** → Deepgram → review in ≤ 20 s
5. Held-out eval: base vs playbook, averaged over 3 runs; Mubit trace panel
6. The wall (100 tiles)

**P1:**
- `report.thistle` sections + edit-with-reason + **send via Gmail**
- one-click escalation email
- the Northwind task, partly trained

**P2:**
- disputes
- coaching notes per agent
- auto-accept per item at ≥ 95%

**Out of scope:** live voice agents, live nudges, real bank data, authentication, telephony.

---

## 9. Demo script (3 minutes, live)

**Before going on stage:**
- API running **without** `--reload`
- the Mubit console on **Try models** in a second tab, with the adapter started beforehand
- the fallback audio file ready
- Gmail open on a phone as Thistle's complaints manager

| Time | Beat | On screen |
|---|---|---|
| 0:00 | *"Thistle Bank sent Harbour 100 calls this week. Our contract checks 2."* The wall lights 2, then **Redress reviews all 100**: complaints, vulnerable customers and critical fails light up. | Wall |
| 0:25 | **Live call.** Sultan (Ellen) rings Abdul (Sam, the agent) on speaker. Sam slips up on purpose. | Recorder |
| 1:05 | **Hang up, and the scorecard lands in seconds:** FAIL · 3 critical fails, each quote ▶ playable. One click sends the escalation to Thistle's manager. | Evaluation form |
| 1:30 | **Label.** On a queued call the AI said "no vulnerability". The analyst overrides it: *"'since my husband passed' = bereavement"*. The rule is created → **Test on archive: 6 calls change** → the agreement meter rises. | Learning / Agreement |
| 2:00 | **Mubit.** `review.thistle` **v2 Passed**, side by side with the big model in Try models. `review.northwind` is still collecting at 12/25: *"one model per client, trained only on its own labels."* | Mubit console |
| 2:25 | **Report.** This week's Thistle report section is drafted. The analyst edits one line with a reason, then sends it, and it **lands in Gmail on the phone**. | Report editor + phone |
| 2:45 | **Money:** coverage 2% → 100% · analyst minutes per call · cost per 1,000 calls, big model vs own model (measured). **"Today's AI QA is configured. Redress is trained, by your analysts, every day."** | Compare |

**Judge Q&A:**
- *"AI QA already exists."* → It's configured, not trained. Analysts' corrections are logged and then thrown away, or improve the vendor's shared model. Ours become this firm's model.
- *"Is 100% accurate?"* → 100% *scored*. Accuracy comes from the random 1% audit and the held-out set, shown on Compare.
- *"Isn't this just a prompt?"* → The rule works immediately. Mubit then distils the corrected calls into a per-client adapter (Try models).
- *"Can banks do their own QA?"* → Yes. The rule is independence (SYSC 6.1). Same product for an in-house QA team.

---

## 10. Build plan
It's Saturday night; code freeze is **Sun 10:00**. **Confirm owners in chat.**

| By | Done when | Owner |
|---|---|---|
| 23:15 | Scorecard + `review.thistle` prompt + JSON schema drafted; routes v3 sent to the UI session | Abdul |
| 23:30 | 100 Thistle calls + 15 Northwind generated; gold labels for the 25 held out | Data (an agent drafts, a human checks) |
| **00:00** | **System prompts FROZEN.** `review.thistle` runs end to end on imported calls | Abdul |
| **00:45** | 75 practice calls sent `full` through Mubit, so training can start before the **01:00 BST limit reset** | Abdul |
| 01:30 | Record → Deepgram → scorecard in ≤ 20 s | **Sultan** ([CALLING.md](docs/CALLING.md)) |
| 03:00 | Evaluation form → corrections → rules → test on archive → agreement | Backend + UI |
| 04:30 | Report sections + edit + Gmail send; escalation email | Sultan (email) + backend |
| 06:00 | Compare: base vs playbook × 3; adapter check in Try models; Northwind partial | Abdul |
| **08:00** | **Feature freeze.** Screen-record every Mubit console beat; rehearse 3 times | All |
| 09:15 | Submit | All |

**Risks:** see [docs/planning/RISKS.md](docs/planning/RISKS.md). The big ones:
- nobody has seen an adapter pass yet;
- training limits;
- held-out leakage;
- prompt edits after 00:00 splitting the task.

---

## 11. Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python -m uvicorn app.main:app --port 8000       # no --reload when demoing
cd web; npm install; npm run dev                                  # http://localhost:3000 (PowerShell, not Git Bash)
```

`.env` (never commit; never paste keys in chat):
```bash
MUBIT_BASE_URL=https://api.mubit.ai/openai/v1
MUBIT_API_KEY=mbt_...
MUBIT_MODEL=gpt-6-luna          # one fixed model for review.* / report.* / rule.induce
BASELINE_MODEL=gpt-6-sol        # closed-model baseline for Compare
DEEPGRAM_API_KEY=...
GMAIL_USER=harbour.assurance.demo@gmail.com
GMAIL_APP_PASSWORD=...          # needs 2-Step Verification on that account
```
Provider keys (OpenAI or Anthropic) go in the **Mubit console under Provider keys**, never in the app.

---

## 12. Ethics and data
- Everything is synthetic: firms, banks, agents, customers and calls. No real recordings.
- PII is redacted before every Mubit call.
- A human checks every escalation and report before it leaves the QA firm. The AI scores; analysts decide.
- Agents are scored on evidence (a quote and timestamp for every answer), never on an unexplained number.
