# Redress: QA on every regulated call, with a model that learns from your analysts

> **Night Shift: $65K Mubit Hackathon, London** · 23–25 October 2026 · <https://luma.com/nightshift-london>
>
> **Track: Recurring tasks** (with Fast refresh as a second fit). Banks check about one customer call in twenty by hand against a compliance scorecard, and nobody checks the rest. Redress scores **every** call through Mubit. On the calls analysts already sample, they now **review and correct the AI's scorecard** instead of filling one in from scratch. Each correction becomes a playbook rule that the very next call is scored with, and every review made with those rules is sent to Mubit as a training example for a small task model the bank owns. Anything that could be a breach goes to a person, because we would rather ask than miss.

All customers, calls and bank data are synthetic. The two live demo callers are teammates reading a script.

---

## 0. For judges: where each criterion is in the code

| Criterion | What to look at | Where |
|---|---|---|
| **Use of Mubit**: a correction turning into a model update | An analyst changes one item and gives a reason. `rule.induce` (a Mubit call) turns it into a general rule, and the playbook moves to v(N+1). Every later `review.call` carries the playbook in its user message and is recorded `full`, so Mubit keeps it as an example of the corrected behaviour for the task adapter. Base (v0) and held-out reviews are recorded `metadata`, so they never train it. Every call shows up in the Mubit trace table with its request ID | [corrections.py](app/learning/corrections.py), [playbook.py](app/learning/playbook.py), [service.py `record_mode`](app/review/service.py), [mubit_client.py](app/llm/mubit_client.py), `/dashboard/mubit` |
| **Usefulness**: a real recurring task | Scoring a call against a scorecard is the same job tens of thousands of times a month in every UK contact centre. Redress reads the exports a QA firm actually receives (Excel/CSV, Amazon Connect Contact Lens JSON, pasted text) as well as live calls, and re-marks a whole month after a single correction | [importers.py](app/capture/importers.py), [Batch routes](app/main.py), `/dashboard/batch` |
| **Technical execution**: it works and holds up under questions | Real calls on two phones (LiveKit), Deepgram transcription, PII scrubbed in code before Mubit and silenced in the stored audio, evidence quotes checked against the transcript, scores and routing in plain deterministic code, and a held-out set with hand-written gold labels that is never trained on. **0 missed breaches in 8 held-out runs** (§14) | [spec.py](app/review/spec.py), [route.py](app/review/route.py), [safety_net.py](app/review/safety_net.py), [redact.py](app/privacy/redact.py), [audio.py](app/privacy/audio.py), [score.py](app/eval/score.py) |
| **Demo**: clear, live, under time | A real phone call is scored seconds after hang-up. The analyst corrects one false alarm in one line, and Redress re-marks the month's other 79 calls with it while the audience watches the escalation count drop | §10 and [docs/DEMO_RUNBOOK.md](docs/DEMO_RUNBOOK.md) |

| Track | How Redress fits |
|---|---|
| **Recurring tasks** (our track) | Call review is a textbook recurring task: same scorecard, same judgement, every call. Corrections from the 5% audit sample become rules immediately and Mubit training examples over time |
| **Fast refresh** | When the rules change (a new mandatory disclosure from Monday, a new client's scorecard), one correction updates the playbook and the next call is scored with it. **Test on archive** re-scores past calls to show what the rule changes before anyone relies on it |
| **Own your intelligence layer** | The groundwork is there: one fixed model per task so Mubit can distil it, held-out evaluation grouped by model, and latency and tokens logged for every call. We have **not** measured an adapter against the provider model, because the adapter hadn't trained by the freeze (§14) |

**Five-minute read of the code:** [mubit_client.py](app/llm/mubit_client.py) (the only module that calls a model) → [service.py](app/review/service.py) (one review, start to finish) → [spec.py](app/review/spec.py) (user message, evidence check, scoring) → [route.py](app/review/route.py) (who sees the call) → [corrections.py](app/learning/corrections.py) and [playbook.py](app/learning/playbook.py) (how a correction becomes a rule) → [score.py](app/eval/score.py) (how we know it works).

---

## 1. The problem and what Redress does

Every regulated customer call (complaints, collections, fees, vulnerable customers) has to meet the bank's standards: identity checked before account details, complaints recognised even when the customer never says the word, vulnerability spotted and supported, no promises the bank can't keep, and the right next steps and timescales. Today QA works like this:

1. The contact-centre system records every call.
2. A small random sample goes to QA analysts. Our research found 1–2% to under 5% is typical in UK contact centres, and the FCA doesn't set a percentage. We use about 5%.
3. An analyst listens to the whole call and fills in a scorecard of weighted items plus critical (auto-fail) items.
4. Analysts meet to calibrate, because they score the same call differently.
5. Failures lead to coaching, remediation (a missed complaint still has to be handled) and reporting under Consumer Duty.

It's slow, it's inconsistent, and around 95% of calls are never checked, so most breaches are never found.

The judgement calls that matter ("that *was* a complaint", "he mentioned his wife died, so that's vulnerability", "'I'm sure we'll refund it' is a promised outcome") already live in analysts' heads. Redress captures them:

1. **Every call** is transcribed, scrubbed of personal data and scored against the bank's scorecard through Mubit.
2. On the calls analysts would have sampled anyway, they **check the AI's scorecard**: agree, or change an answer and say why in a sentence.
3. Each correction becomes a **rule** in a new playbook version, which every later review includes straight away.
4. Reviews made with those rules are **Mubit training examples**, so a small task model learns how this bank scores calls.
5. The other ~95% of calls are scored by the improving system. **Anything that might be a breach goes to a person.**

Every escalated call, every audit-sample call and every decision about a colleague stays with a person. Redress drafts the score and people decide.

**In one line:** without Mubit, AI scores calls. With Mubit, it learns how your QA team scores them.

---

## 2. Event

| Item | Detail |
|---|---|
| Event | Night Shift: $65K Mubit Hackathon, London · Fri 23 Oct 17:00 → Sun 25 Oct 14:00 |
| Brief | Route LLM calls through Mubit and turn corrections into model updates for a recurring task |
| Freeze | Sun 10:00 code freeze · 10:30 expo judging · 12:30 finalist demos · 13:30 awards |

---

## 3. Mubit: what we verified, and the traps

Everything here was checked against <https://docs.mubit.ai/llms-full.txt>, live calls with our key, and written answers from the Mubit team.

### 3.1 What Mubit is
Mubit is a proxy between the app and the model provider. You change the base URL and use a Mubit key, and nothing else changes. Mubit:
1. passes each call to the provider and records it (request and reply, by default);
2. groups similar calls into **tasks**;
3. keeps some of them as **kept examples** (duplicates aren't kept);
4. once a task has **25 kept examples**, trains an **adapter**, a small open model for that one task, graded on how closely it matches the provider model's answers;
5. lets you compare a passing adapter with the provider model in the console's **Try models**.

The adapter learns to copy the provider model on our inputs. That is exactly why analyst corrections reach the model: the playbook rules are part of the input, so the provider's corrected answers are what the adapter learns.

### 3.2 Verified API facts

| Fact | Detail |
|---|---|
| Base URL | OpenAI SDK `https://api.mubit.ai/openai/v1` (Anthropic SDK `https://api.mubit.ai/anthropic`, no `/v1`) |
| Key | Mubit key (`mbt_…`) as the SDK's API key, and nothing else. A provider key or a stray extra credential gets a `401` |
| Structured outputs | `response_format: {type: "json_schema", strict: true}` works through Mubit |
| Request ID | Every response has the header `x-middleware-request-id` (`mreq_…`), read with `with_raw_response` |
| Who served it | `response.model` |
| What Mubit keeps | Header `x-middleware-record`: `full` (default, can become a training example), `metadata` (logged without content, never trained on), `off` |
| Sessions | OpenAI rejects `metadata.session_id` unless `store=true`, and we don't want OpenAI storing calls, so we don't send it |
| CORS | None. Mubit is called from the server only |

### 3.3 What Mubit does not do (confirmed by the Mubit team)
- **There's no API for corrections or feedback.** Rating a call Bad in the console doesn't remove it from training; only `x-middleware-record: metadata` keeps a call out. So our corrections reach Mubit as corrected *behaviour* (reviews made with the playbook), not as labels.
- **Adapters can't be called from code.** They have no model ID, and the only place to run one is Try models in the console.
- **There's no custom grading.** A version is graded on how closely it matches the provider model.

### 3.4 How tasks form (this decides whether an adapter ever trains)
Calls are one task when they share **model, system prompt, tools, tool choice and output format**. The user message, `temperature` and `max_tokens` don't count. So Redress:
- uses **one fixed model** per task (`MUBIT_MODEL`), because the same prompt on two models makes two tasks;
- **froze** the system prompts ([prompts/](app/llm/prompts/)) and the JSON schema ([call_review.json](app/llm/schemas/call_review.json)) early, because editing either starts a new task at 0 of 25;
- puts **everything that varies** (playbook rules, redacted transcript) in the user message;
- writes the **scorecard into the `review.call` system prompt**, so each bank's scorecard is its own task and its own adapter.

### 3.5 Kept examples
Training starts at 25 kept examples, and the console moves through Collecting examples → Reviewing examples → Training → Testing. Duplicates don't count, and the count updates only after Mubit reviews examples, which can lag by hours. That's why we generated 80 varied practice calls and sent them through early.

### 3.6 The integration
```python
# app/llm/mubit_client.py: the only module that calls a model
raw = client.chat.completions.with_raw_response.create(
    model=model or MUBIT_MODEL,
    messages=[{"role": "system", "content": system},   # fixed per task
              {"role": "user", "content": user}],      # everything that varies
    response_format={"type": "json_schema", "json_schema": {"name": ..., "strict": True, "schema": schema}},
    extra_headers={"x-middleware-record": record},     # "metadata" = never trained on
)
```
Each call is logged to the `traces` table with task, request ID, served-by model, record mode, latency and tokens, which is what the Mubit page shows.

### 3.7 Lessons from our first prototype
- Don't trust chatbot answers about Mubit. We were told about `record_outcome()`, memory calls and automatic adapter routing; the endpoints returned `unknown_route` and the Mubit team confirmed none of it exists today.
- Score at base before writing rules. Don't guess where the model fails. On Redress the base model never missed a breach; its real weakness is over-flagging.
- A narrow rule set can make things worse. Guardrail rules for the non-negotiables keep a broad rule from loosening a critical item.
- Single runs are noisy, so every number we quote is a mean over repeated runs.
- Make held-out calls `metadata`-only **in code** ([service.py `record_mode`](app/review/service.py)), not by remembering.
- `uvicorn --reload` kills background work, so the API runs without it.

---

## 4. How it works

### 4.1 The flow
```text
 Customer ⇄ Bank colleague    (demo: two phones on LiveKit; production: the contact-centre recorder or its export)
        │ stereo recording, one channel per speaker
        ▼
 ┌──────────────────────────────── Redress API (FastAPI, SQLite) ─────────────────────────────────┐
 │ 1 CAPTURE     WAV saved locally, or a batch import (Excel/CSV, Amazon Connect JSON, text)       │
 │ 2 TRANSCRIBE  Deepgram nova-3 → utterances [agent | customer, start_s, end_s, confidence]       │
 │ 3 TIDY        drop cross-talk echo, merge fragments, write dates the way QA does                │
 │ 4 SCRUB       PII redacted in code; the same words silenced in the stored WAV                   │
 │ 5 REVIEW      review.call via Mubit → per-item answer, evidence quotes, confidence              │
 │               evidence check (plain code): every quote must exist in the transcript             │
 │ 6 SCORE       plain code: weighted score, critical fails, pass/fail, risk tier                  │
 │ 7 ROUTE       plain code: breach → escalate · uncertain → analyst · 5% → audit · rest → auto    │
 │ 8 CORRECT     analyst agrees or changes each item with a one-line reason                        │
 │ 9 LEARN       rule.induce via Mubit → playbook vN → every later review includes the rules       │
 │               reviews made with vN (record=full) → Mubit kept examples → task adapter           │
 └─────────────────────────────────────────────────────────────────────────────────────────────────┘
        ▲ REST, polled every 1–5s
 Web app (Next.js): landing · overview · live call · batch · evaluation form · learning · proof · Mubit
```

### 4.2 Capture and transcription
We assume high-fidelity audio. Every score depends on the transcript, and a misheard "I was in hospital" is a missed vulnerability. Real contact centres record cleanly, usually one track per speaker, and we design for that.

| Setup | How | Speaker labels |
|---|---|---|
| **Two phones** (the demo) | The laptop opens the line on the Live call page. The customer's phone opens `/call/customer` and rings, and the colleague's phone opens `/call/agent` and answers. The phone pages are deployed on Vercel for HTTPS (the mic needs it). The laptop joins the LiveKit room and records one stereo WAV, customer left and colleague right, and uploads it on hang-up ([line-server.ts](web/lib/line-server.ts), [line.ts](web/lib/line.ts), [api/line](web/app/api/line/)) | Exact, from the channel |
| **Laptop mic** | **Record call** with a phone on speaker next to the laptop | Deepgram diarisation; **Swap speakers**, or click one line's label to flip it, then **Re-score** |
| **Upload or import** | **Upload file** on Live call, or a whole month on **Batch** | As recorded or as exported |

- Deepgram pre-recorded (`nova-3`, diarize, utterances, smart formatting, word timestamps) runs after hang-up. Two-channel recordings use multichannel mode ([stt.py](app/capture/stt.py)).
- [tidy.py](app/capture/tidy.py) drops the echo when each phone's mic picks up the other person, merges one speaker's fragments into a line, and turns spoken dates into "19 Dec 2004" so the DOB redaction can catch them.
- **Low STT confidence is a routing signal.** If the call's transcription confidence is below `REDRESS_STT_MIN_CONFIDENCE` (0.75), it goes to an analyst, because we don't score what we couldn't hear.
- Speech-to-text isn't an LLM task, so it calls Deepgram directly.

### 4.3 PII scrubbing (before anything reaches Mubit)
Mubit records request and reply content by default, so Redress behaves as a bank would even on synthetic data:

1. **Redaction in plain code before any model call** ([redact.py](app/privacy/redact.py)): card numbers (with a Luhn check), sort codes, account numbers, dates of birth, postcodes, phone numbers, emails, addresses, and customer names from [customers.json](data/customers.json). Values become typed tokens like `[CARD]`, `[DOB]` and `[NAME]`. The review needs to know that an identity check happened, not what the date of birth was.
2. **The stored recording is redacted too.** After transcription every word inside a redacted span is silenced in the saved WAV using Deepgram's word timestamps ([audio.py](app/privacy/audio.py)), and the evaluation form says how many moments were silenced. Compressed uploads (WebM, MP3) are left as they are, and the form says so.
3. **Raw audio and the raw transcript stay on the laptop.** Only redacted text is sent to Mubit. The evaluation form's *What Mubit saw* toggle shows exactly what was sent.
4. **Held-out and base reviews** use `x-middleware-record: metadata`, so Mubit keeps no content for them.

### 4.4 The review (one Mubit task)
- **System prompt (fixed):** reviewer instructions plus the bank's scorecard ([review_call.md](app/llm/prompts/review_call.md)).
- **User message (varies):** the playbook rules for version N plus the redacted transcript as `[start_s] AGENT|CUSTOMER: text` ([spec.py](app/review/spec.py)).
- **Output (strict JSON):** for every item an `answer` (`yes`, `no`, `na` or `unsure`), short reasoning, evidence quotes with timestamps, and a confidence, plus complaint, vulnerability and a summary.
- **Afterwards, in plain code:** quotes that don't appear in the transcript are dropped and the item becomes `unsure`. Then the weighted score, critical fails, pass/fail and risk tier are computed. The model never sets the score.

### 4.5 Conservative by design: a missed breach is the worst outcome
| Mechanism | Rule (plain code, [route.py](app/review/route.py)) |
|---|---|
| **A pass needs evidence** | A critical item is only `yes` with a quote showing the compliant behaviour. With no quote it becomes `unsure` |
| **`unsure` is allowed and routed** | The prompt tells the model to say `unsure` rather than guess, and any critical `unsure` goes to an analyst |
| **Confidence thresholds** | A critical item below 0.8, or a scored item below 0.6, goes to an analyst |
| **Keyword safety net** | Independent of the model ([safety_net.py](app/review/safety_net.py)): vulnerability cues ("hospital", "passed away", "lost my job"…) and complaint cues ("not happy", "unacceptable"…). If a cue fires and the model found nothing, the call goes to an analyst |
| **STT quality** | Low transcription confidence goes to an analyst |
| **Confident breach** | A critical `no` with evidence and confidence of at least 0.8 is escalated at once (still checked by a person, just first) |
| **Audit sample** | A stable hash-based 5% of calls go to an analyst whatever the model says, the same sample banks take today, and it keeps our accuracy honest |
| **Everything else** | Auto-scored and counted in coverage |

So that it stays useful rather than flagging everything, we track the **human queue rate** next to critical recall, and per-item AI-vs-analyst agreement on the Learning page. Thresholds are set on practice calls, never on the held-out set.

### 4.6 The analyst's job: review the AI, don't redo it
1. Open a call from the queue or the batch. The transcript plays the audio from any line, flagged lines glow, and the AI scorecard is pre-filled with answers, quotes and confidence, critical items first.
2. For each item, agree, or pick a different answer and give a one-line reason (presets are offered).
3. **Submit.** Each changed item becomes a correction ([corrections.py](app/learning/corrections.py)), and agreements count towards per-item agreement.

### 4.7 The learning loop: how a correction becomes a model update
```text
Analyst correction (item, before, after, reason, transcript excerpt)
   ├─► rule.induce (Mubit) → a general rule {rule, applies_when, keywords} → playbook vN
   ├─► IMMEDIATE: every later review.call includes playbook vN in the user message
   │              → the next call, and on Batch the rest of the month, is scored with the rule
   └─► MODEL UPDATE: reviews made with vN ≥ 1 on practice and live calls are recorded full
                     → Mubit kept examples → 25 kept → the review.call adapter trains → Try models
Base (v0) and held-out reviews are recorded metadata → never training data
```
- **The 5% audited calls** are where corrections come from: the analysts' existing workload, made faster.
- **The other 95%** get every rule straight away, and the adapter once it passes.
- **Re-mark the month:** on Batch, **Score the rest** re-scores every unchecked call with the latest playbook, starting with calls that look like the newest correction (its keywords and phrases from the corrected quote), so the effect shows within seconds.
- **Test on archive** re-scores past calls a rule might affect and shows before → after, which is how a QA lead checks a rule before trusting it ([test_on_archive.py](app/learning/test_on_archive.py)).
- **Guardrail seeds** ([seed.jsonl](data/corrections/seed.jsonl)) pin the non-negotiables (a promised refund is always a C3 fail; account details before ID is always a C4 fail) so a broad rule can't loosen a critical item.

---

## 5. The scorecard (Thistle Bank, fictional)

| # | Item | Type | Basis |
|---|---|---|---|
| C1 | Complaint recognised and logged, even if the word "complaint" wasn't used | **Critical** | FCA DISP definition of a complaint |
| C2 | Vulnerability recognised and support offered | **Critical** | FCA FG21/1 |
| C3 | No promise of an outcome and no misleading statement | **Critical** | Consumer Duty: consumer understanding |
| C4 | Identity verified before account details were discussed | **Critical** | Bank security policy |
| S1 | Next steps and the right timescale explained (8 weeks, or 15 business days for payment services) | 20 pts | FCA DISP 1.6 |
| S2 | Checked the customer understood | 20 pts | Consumer Duty |
| S3 | Information given was accurate | 20 pts | Bank policy |
| S4 | Empathy and tone | 20 pts | Service standard |
| S5 | Took ownership and agreed a follow-up | 20 pts | Service standard |

A call passes with no critical fail and a score of 80 or more. The scorecard is in [scorecard.json](data/scorecard.json) and is written into the `review.call` system prompt. The regulatory references are simplified summaries.

---

## 6. Mubit tasks
| Task | System prompt (fixed) | User message (varies) | Output | Record mode |
|---|---|---|---|---|
| `review.call` | Reviewer instructions and scorecard ([review_call.md](app/llm/prompts/review_call.md)) | Playbook vN and redacted transcript | Per-item answer, reasoning, evidence, confidence; complaint; vulnerability; summary | `full` at v ≥ 1 on practice and live calls; `metadata` at v0 and on held-out calls |
| `rule.induce` | Rule writer ([rule_induce.md](app/llm/prompts/rule_induce.md)) | Item, before, after, reason, transcript excerpt | `{rule, applies_when, keywords}` | `full` |
| `data.generate` (offline) | Synthetic call writer ([generate_calls.py](scripts/generate_calls.py)) | A scenario spec | A transcript | `metadata` |

Both product tasks use one fixed model, `MUBIT_MODEL` (default `gpt-6-luna`), with `reasoning_effort` `low` for reviews.

---

## 7. Data model, API and web app

### SQLite tables ([db.py](app/db.py))
```text
calls(id, source: live|upload|synthetic|demo|import, split: practice|heldout|live, agent_name, customer_name,
      audio_path, audio_muted, duration_s, stt_confidence, status, error, batch_id, created_at)
utterances(call_id, idx, speaker: agent|customer, text_raw, text_redacted, start_s, end_s, confidence)
reviews(call_id, run_id, playbook_version, request_id, model, served_by, record_mode, latency_ms, tokens,
        output_json, items_json, issues_json, score, pass, critical_fails, risk_tier)
queue(call_id, review_id, kind: breach|analyst|audit|auto, reasons_json, audit, due_at, done)
evaluations · corrections · playbook_versions · agreement · runs · traces · batches
```

### API ([main.py](app/main.py))
```text
GET  /api/status                       Mubit and Deepgram config, playbook version, training examples sent
GET  /api/scorecard
POST /api/calls                        multipart audio → Deepgram → tidy → redact → review → route (background)
POST /api/calls/import                 JSON transcripts
POST /api/demo/scripts/{id}            load demo_call1 / demo_call2 as a text call (rehearsal and fallback)
GET  /api/calls · GET /api/calls/{id} · GET /api/calls/{id}/audio
POST /api/calls/{id}/review            re-score now (optionally at an older playbook version)
POST /api/calls/{id}/utterances/{idx}/flip · POST /api/calls/{id}/swap-speakers
POST /api/calls/{id}/evaluation        analyst answers → corrections → rule.induce → new playbook version
POST /api/batches                      import a month's export (xlsx, csv, Amazon Connect JSON, text) and score it
GET  /api/batches · GET /api/batches/{id}
POST /api/batches/{id}/finish          re-score every unchecked call with the latest playbook, similar calls first
GET  /api/wall · GET /api/queue · GET /api/learning
POST /api/corrections/seed             load the guardrail seeds as a playbook version
POST /api/rules/{correction_id}/test   test on archive: before vs after
POST /api/eval · GET /api/runs · GET /api/compare   held-out runs (always metadata) and averaged metrics
GET  /api/traces                       the Mubit trace table
POST /api/demo/reset                   clear live calls, checks and analyst corrections; keep synthetic calls and seed-only playbooks
```

### Pages (`web/`, Next.js 16.4.3, React 19, Tailwind 4)
| Page | What it's for |
|---|---|
| `/` | The pitch, scrolled or driven by ↑/↓ and 1–5: Home, Problem (press L to flip the 100-call wall from 5 heard to all), How it works, Proof (live held-out numbers), Mubit (collecting → training → adapter) |
| `/dashboard` | Overview: stats, the wall (one tile per call, coloured by risk), the queue (most urgent first, ten at a time) |
| `/dashboard/live` | Open the phone line, or record on the laptop mic, or upload. Hang-up → transcript → scorecard with the four findings |
| `/dashboard/batch` | Import the month's export, check a few calls together (suggested order), then let Redress score the rest with what it learned |
| `/dashboard/calls/[id]` | The evaluation form: audio from any line, *What Mubit saw*, AI scorecard, corrections with reasons, test the new rule, compare with an earlier version |
| `/dashboard/learning` | Playbook versions, rules, corrections, AI-vs-analyst agreement per item |
| `/dashboard/proof` | Held-out metrics per version (mean and range), per-call barcode, **Run 3× base vs latest** |
| `/dashboard/mubit` | Gateway settings, training examples sent, adapter stages, live trace table |
| `/call/customer`, `/call/agent` | The two phones (deployed to Vercel) |

The look follows the HTML references in [design/](design/), which are visual reference only.

---

## 8. Technology and repo layout

| Layer | Choice |
|---|---|
| LLM gateway | **Mubit** via the OpenAI SDK; strict JSON; one fixed model per task |
| Speech-to-text | **Deepgram** pre-recorded, nova-3; multichannel for the phone line, diarisation otherwise |
| Phone line | **LiveKit** Cloud (free plan): `livekit-client` in the browser, `livekit-server-sdk` in Next route handlers. The laptop mixes the two remote tracks into stereo WAV |
| Backend | Python 3.11+, FastAPI, SQLite, openpyxl |
| Frontend | Next.js 16.4.3, React 19, Tailwind 4 |

```text
mubit-hack/
├── README.md · requirements.txt · .env.example
├── docs/DEMO_RUNBOOK.md          # links, timings, what to do when something breaks
├── design/                       # HTML prototypes: visual reference only
├── app/
│   ├── main.py · config.py · db.py · demo.py
│   ├── llm/mubit_client.py       # the ONLY module that calls a model
│   ├── llm/prompts/ · llm/schemas/   # frozen system prompts and the strict JSON schema
│   ├── capture/                  # stt.py (Deepgram), ingest.py, tidy.py, importers.py (Excel/CSV/Connect/text)
│   ├── privacy/                  # redact.py (text), audio.py (silence the same words in the WAV)
│   ├── review/                   # service.py, spec.py, route.py, safety_net.py
│   ├── learning/                 # corrections.py, playbook.py, test_on_archive.py
│   └── eval/                     # score.py (vs gold, no LLM judge), runner.py (repeated runs)
├── data/
│   ├── scorecard.json · customers.json
│   ├── calls/practice/ (80) · calls/heldout/ (25)
│   ├── eval/gold.jsonl           # held-out labels, written before any run
│   ├── corrections/seed.jsonl    # guardrail seeds
│   ├── batches/                  # Thistle's October export (xlsx and csv), built by scripts/make_batch.py
│   └── demo/                     # the two call scripts
├── scripts/                      # generate_calls, import_calls, seed_playbook, warm_mubit, run_eval, make_batch, smoke_mubit, reset_demo
└── web/                          # Next.js app and phone pages
```

---

## 9. Synthetic data and evaluation

- **Label first:** each call starts as a scenario spec (the customer's situation and what the colleague does right or wrong on each item), and the transcript is generated from it. The spec is the gold label. The held-out labels in [gold.jsonl](data/eval/gold.jsonl) were written before any run.
- **Mix:** 80 practice calls (Mubit warm-up, corrections, the October batch) and 25 held-out calls (gold, `metadata` only). Many contain a hard case: a complaint without the word, vulnerability mentioned in passing, a promised refund, the wrong deadline, account details before ID, or a clean call that looks risky.
- **Scoring is deterministic** ([score.py](app/eval/score.py)). No LLM judges the LLM. A gold breach counts as caught if the model failed the item or the call went to a person anyway.

| Metric | Why |
|---|---|
| **Critical recall** and the false-negative count | The headline: a missed breach is the worst outcome |
| Flag precision | Over-flagging costs analyst time |
| **Human queue rate** | Conservatism has a price, so we keep it bounded |
| Item accuracy vs gold | Where the model and the labels differ |
| Complaint and vulnerability recall | The two items people miss most |
| Review latency (median) | Scorecard within seconds of hang-up |

---

## 10. Demo (3 minutes, live)

The full run, links and fallbacks are in [docs/DEMO_RUNBOOK.md](docs/DEMO_RUNBOOK.md). In short:

1. **Home → Problem:** banks hear one call in twenty. Press L and 5 tiles become 100.
2. **Live call:** open the line. The customer's phone rings Thistle Bank and the colleague's phone answers, and they play the script ([call1.json](data/demo/call1.json)). Hang up, and about 15–20 seconds later the scorecard shows **FAIL · C1, C2, C3**.
3. **Evaluation form:** press ▶ on the C2 quote and you hear the customer say she was in hospital. The AI is right here, so the analyst just confirms.
4. **Batch:** that call is one of 81 in Thistle's October batch, and v0 escalated about 55 of them.
5. **Call p044:** the AI failed C3 because the colleague said a fee can never be refunded. The analyst changes it to pass with the reason *"Saying a fee can't be refunded is information, not a promised outcome."* That becomes a rule and playbook v1.
6. **Batch → Score the rest with playbook v1:** the calls like p044 are re-marked first, and **Escalate now** drops while the audience watches. In rehearsal it went from 56 to 50, and the false alarm cleared on 4 of 7 similar calls. The model isn't deterministic, so expect roughly that.
7. **Mubit page:** every call through Mubit with its request ID, and the reviews made with v1 are training examples.

**Questions we expect:**
- *What if the transcript is wrong?* We assume high-fidelity recordings, and each phone is its own channel. Low STT confidence sends the call to a person, and one click flips a mislabelled line.
- *What about false negatives?* 0 missed out of 22 breaches on the held-out set across 8 runs. Critical items need evidence to pass, `unsure` goes to a person, there's an independent keyword safety net, and 5% are audited at random.
- *Isn't this an LLM judging people?* It drafts scores and analysts decide. Anything that affects a colleague stays human.
- *PII?* Redacted in code before Mubit (see *What Mubit saw*), silenced in the stored audio, and held-out runs aren't stored at Mubit.
- *Isn't it just a prompt?* The playbook applies corrections at once and re-marks a month in minutes. Mubit then distils the corrected reviews into a task adapter the bank owns.
- *Has the adapter trained?* Not by the freeze (§14). We explain where it stands rather than fake it.

---

## 11. Setup

Python 3.11+ and Node 20+. Commands are for PowerShell on Windows (npm misbehaved under Git Bash on our machine).

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env                                        # set MUBIT_API_KEY and DEEPGRAM_API_KEY
.\.venv\Scripts\python -m scripts.smoke_mubit                 # Mubit and Deepgram reachable?
.\.venv\Scripts\python -m uvicorn app.main:app --port 8000    # no --reload: it kills background scoring
cd web; npm install; npm run dev                              # http://localhost:3000 and /dashboard
```

**For the phone line,** put `LIVEKIT_URL`, `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` in `web/.env.local` and in the Vercel project, then deploy the phone pages from `web/` with `vercel deploy --prod`. The laptop must use `localhost`, because only it opens the line and records.

**A fresh database** (the transcripts and the batch files are already in the repo):
```powershell
.\.venv\Scripts\python -m scripts.import_calls                # import practice and held-out calls, score practice at the latest playbook
.\.venv\Scripts\python -m scripts.seed_playbook               # optional: guardrail seeds → a playbook version
.\.venv\Scripts\python -m scripts.warm_mubit                  # re-score practice calls at the latest version (training examples)
.\.venv\Scripts\python -m scripts.run_eval --repeats 3        # held-out: base vs latest, averaged
.\.venv\Scripts\python -m scripts.make_batch                  # rebuild data/batches/ from the practice calls
.\.venv\Scripts\python -m scripts.reset_demo                  # before a demo run (--all clears everything)
.\.venv\Scripts\python -m scripts.generate_calls --only-missing   # regenerate any missing synthetic transcripts
```
Then import `data/batches/thistle-october-2026.xlsx` on the Batch page.

**Settings** (`.env`; restart the API after a change): `MUBIT_MODEL` (default `gpt-6-luna`; changing it starts new Mubit tasks), `REVIEW_REASONING_EFFORT` (default `low`: about 13.5s per review, against 18.6s at the default and 10s at `none`), `DEEPGRAM_MODEL` (`nova-3`), `REDRESS_MAX_PARALLEL` (calls scored at once, default 4; we demo with 8), `REDRESS_AUDIT_RATE` (0.05), `REDRESS_CRITICAL_CONFIDENCE` (0.8), `REDRESS_SCORED_CONFIDENCE` (0.6), `REDRESS_STT_MIN_CONFIDENCE` (0.75), `REDRESS_HELD_OUT_RECORD` (`metadata`).

Keys live in `.env` only, which is gitignored. Provider keys never go in the app: they're set in the Mubit console under Provider keys.

---

## 12. Limits, stated plainly
| Limit | How we handle it |
|---|---|
| High-fidelity audio is assumed | One channel per speaker in the demo; low STT confidence goes to a person |
| False negatives | §4.5: evidence to pass, `unsure`, thresholds, safety net, random audit, recall as the headline |
| Over-flagging | The base model escalates about 55 of 80 batch calls. That's what calibration by analysts fixes, and the queue rate is tracked next to recall |
| Mubit | No correction API; adapters run only in Try models; prompt edits reset a task; kept examples lag (§3.3–3.5) |
| The model isn't deterministic | Every quoted number is averaged over repeated runs; on stage we don't promise exact counts |
| LLM judging people | Scores are drafts; people decide; quotes and timestamps make every score checkable |
| Regulatory summaries | Our DISP, Consumer Duty and FG21/1 summaries are simplified |
| Phone pages | Anyone with the link can ring the line while it's open; the Vercel site is deployed by hand |

## 13. Ethics and data
- Every customer and call is synthetic, and the live callers are teammates reading a script.
- Redress assists QA. It never takes action on a colleague or a customer by itself.
- Calls carry the usual notice that they're recorded for quality and training.

---

## 14. Measured results (25 Oct 2026)

**Held-out set: 25 calls containing 22 critical breaches (18 calls with at least one), 4 runs per version, never trained on:**

| | Base (v0) | Playbook v1 (guardrail seeds) |
|---|---|---|
| Breaches caught (system critical recall) | **100%** in every run | **100%** in every run |
| Missed breaches | **0** | **0** |
| Flag precision | 89.9% (88–96) | 89.0% (85–92) |
| Sent to a human | 81% (80–84) | 78% (76–84) |
| Item accuracy vs gold | 90.9% (91–92) | 90.9% (89–92) |
| Review time (median) | about 12s | about 12s |

- Across 8 runs the system had 176 chances to miss a breach and missed none, so the conservative design isn't costing recall. The guardrail seeds cover things the base model already got right, so v1 is within noise of base. The room to improve is precision, which is what analyst corrections like the p044 rule target.
- The queue rate is high because the synthetic set is dense with lapses (18 of 25 calls really breach). In a real centre most calls are compliant.
- **Batch re-mark (rehearsal):** one correction on p044 took Escalate now from 56 to 50 across the October batch, and cleared the false alarm on 4 of 7 similar calls.
- **Mubit:** 95 `review.call` reviews recorded `full` (practice reviews at a playbook version and rehearsal calls) and 202 recorded `metadata` (base and held-out). At the freeze the console showed the `review.call` task under **Reviewing examples**, with no adapter version yet, so we haven't compared an adapter with the provider model.
