# Redress architecture (v3: QA for outsourced QA firms)

**In short:**
- Call recordings from each bank client are transcribed and scored by an AI reviewer against that bank's scorecard: **100% of calls**.
- The riskiest and least-certain calls go to an analyst, who confirms or overrides each item with a reason.
- Overrides become rules straight away and Mubit training examples over time.
- Each week, an AI writes the client report section by section; the analyst edits and sends it.
- **Each bank gets its own Mubit review task and its own report task, so its own models.**

Owner of this doc: Abdul. Change it and the routes in §5 together, never one without the other.

---

## 1. The flow

```text
 BANK CLIENT (Thistle Bank, Northwind Finance)
   call recordings ─────────────┐            (demo: live role-play recorded on the laptop + 100 synthetic transcripts)
                                ▼
 ┌────────────────────────── Redress API (FastAPI, SQLite) ───────────────────────────────┐
 │ 1 INGEST     upload audio → Deepgram (pre-recorded, diarize) → utterances [agent|customer]│
 │              or import JSON transcripts · PII redaction (regex) before any model call     │
 │ 2 REVIEW     review.<client> (Mubit) → scorecard items + evidence + risk tier + confidence│
 │ 3 ROUTE      plain code: critical → escalate now · high / low-confidence → analyst queue  │
 │              · random 1% → audit queue · rest → auto-accepted                            │
 │ 4 LABEL      analyst confirms / overrides each item + reason ─► corrections              │
 │ 5 LEARN      rule.induce (Mubit) → playbook_<client> vN ─► next calls include the rules   │
 │              "test on archive": re-run affected calls with vN, show before → after        │
 │              agreement per item (AI vs analyst on audited calls) → auto-accept list       │
 │ 6 REPORT     report.<client> (Mubit), one call per section/finding → analyst edits + reason│
 │              ─► report rules → next report · Gmail SMTP → client's complaints manager     │
 │ app/llm/mubit_client.py ─────────────────────────────► Mubit gateway ─► provider model   │
 └───────────────────────────────────────────────────────────────────────────────────────────┘
                 ▲ REST, polled every 1–2 s
   Web app (Next.js): Wall · Queue · Evaluation form · Agreement · Report editor · Learning · Mubit panel
```

---

## 2. Mubit tasks (one model per task, fixed; system prompts frozen by 00:00)

A Mubit task is the combination of **system prompt + model + output format** (README §3.4). So:
- **putting the client's scorecard in the system prompt** gives **one task per bank**, which means one adapter per bank, trained only on that bank's calls;
- **putting the client's report template in the system prompt** gives one report task per bank.

| Task | System prompt (fixed) | User message (varies) | Output (strict JSON) | Record mode |
|---|---|---|---|---|
| `review.thistle` | [`app/llm/prompts/review_thistle.md`](../app/llm/prompts/review_thistle.md): reviewer instructions + **Thistle's scorecard** (C1–C4, S1–S5) | `spec.build_user_message()`: `PLAYBOOK (...)` + `TRANSCRIPT` lines `[start_s] AGENT/CUSTOMER: text` | [`call_review.json`](../app/llm/schemas/call_review.json): `{complaint{expressed, category, evidence[]}, vulnerability[{driver, evidence[]}], clock, scorecard{C1..S5: {reasoning, answer, evidence[{quote, start_s}], confidence}}, summary}`. **The score, pass/fail and risk tier are computed in code** (`spec.score`) | practice and live calls: `full` · held-out: `metadata` |
| `review.northwind` | Same reviewer instructions + **Northwind's scorecard** | Same | Same | Same. **Left at about 12/25 on purpose**, to show "one model per client" |
| `report.thistle` | Report writer + **Thistle's report template and tone** | **One section's inputs**: the stats for that section (computed in code) + evidence excerpts + report playbook vN | `{title, body, evidence_call_ids:[...]}` | `full` |
| `rule.induce` | Rule writer (shared) | The correction (before, after, reason, context) | `{rule, applies_when, keywords}` | `full` |

**Frozen at 00:00 (don't edit after):**
- `app/llm/prompts/review_thistle.md`
- `review_northwind.md`
- `app/llm/schemas/call_review.json`
- the user-message layout in `app/review/spec.py`
- the model (`MUBIT_MODEL`)

When porting Redline's `mubit_client.py`:
- add `"review.thistle": "review_thistle.md"` and `"review.northwind": "review_northwind.md"` to `TASKS`;
- keep the schema name convention (`review_thistle`);
- run every review through `spec.verify_evidence()` then `spec.score()`.

Smoke test: `python -m scripts.try_review` (it uses `record=metadata`, so nothing is trained on).

**Why reports are written one section at a time:**
- Mubit refuses "examples too long to train on" (Mubit docs).
- One weekly report wouldn't reach 25 examples before the demo.
- One call per **finding, agent coaching note or section** gives dozens of short, varied examples a week.

**How the learning works (README §3.7, confirmed with the Mubit team):**
- There is **no corrections API**, and Mubit grades adapters on how closely they match the big model.
- So corrections reach the model like this: the analyst's override becomes a rule, the rule goes in the user message of later calls, the big model's answers become correct, and Mubit trains the next adapter version on those.
- Each new version (v1, v2, v3) is tested by Mubit before it passes. "Same model or a new one?" **The same task gets a new version.**
- Today the adapter runs only in Mubit's Try models, not from our app.

---

## 3. Routing (plain code)

| Condition | Queue | Why |
|---|---|---|
| Any critical item failed, or `risk_tier = critical` | **Escalate now**: a one-click email to the client | Aveni tier: "immediate investigation and escalation" |
| `risk_tier = high`, **or** any item confidence < 0.7 | **Analyst queue** (deadline: 24 h) | Prioritised human review |
| Not routed above, and picked by `random() < 0.01` | **Audit queue** | Keeps the agreement figure unbiased |
| Everything else | **Auto-accepted** | Covered, scored, and in the report |
| An item whose agreement is ≥ 95% over its last 50 audited calls | That item auto-accepts even on routed calls | The AI is "calibrated" for that item |

---

## 4. Data model (SQLite)

```text
clients(id, name, scorecard_json, report_template, contact_email)
calls(id, client_id, agent_name, source:"upload"|"import", audio_path, duration_s, created_at, heldout bool)
utterances(call_id, idx, speaker:"agent"|"customer", text, start_s, end_s)
reviews(id, call_id, playbook_version, request_id, model, latency_ms, output_json, created_at)
queue(call_id, kind:"escalate"|"analyst"|"audit"|"auto", reason, due_at, done bool)
evaluations(id, call_id, analyst, items_json, comments, submitted_at)
corrections(id, call_id|report_section_id, field, before, after, reason, created_at)
rules(id, client_id, task:"review"|"report", text, applies_when, keywords, from_correction, version)
agreement(client_id, item_id, n, agreed, pct, updated_at)
reports(id, client_id, period, status:"draft"|"sent", sent_at, message_id)
report_sections(id, report_id, kind, title, body, evidence_json, version)
traces(ts, task, request_id, model, latency_ms, record, tokens_in, tokens_out)
eval_runs(id, label:"base"|"playbook"|"adapter", client_id, metrics_json, per_call_json, created_at)
```

---

## 5. Routes (v3). Copy these verbatim to the UI agents

```text
GET  /api/clients                    → [{ id, name, agreement_pct, calls_this_week }]
POST /api/calls                      multipart { audio, client_id, agent_name } → { call_id }           (record → transcribe → review)
POST /api/calls/import               { client_id, calls:[{ agent_name, utterances:[...] }] } → { count }
GET  /api/calls/{id}                 → { id, client_id, agent_name, duration_s, audio_url,
                                         utterances:[{ speaker:"agent"|"customer", text, start_s, end_s }],
                                         review:{ overall_pct, pass, critical_fails:[id], risk_tier, confidence, summary,
                                                  items:[{ id, label, kind:"critical"|"scored", weight, answer:"yes"|"no"|"na",
                                                           quote, start_s, rule, confidence }],
                                                  complaint:{ is_complaint, category, quote }, clock,
                                                  vulnerability:[{ driver, quote, start_s }],
                                                  request_id, model, playbook_version },
                                         evaluation:{ analyst, items:[{ id, answer, agreed, reason }], comments, submitted_at } | null,
                                         queue:{ kind, reason, due_at } }
GET  /api/wall?client_id=            → { total, sampled_ids:[id], stats:{ complaints, vulnerable, critical, found_by_sample, found_by_redress },
                                         tiles:[{ call_id, risk_tier, pass, complaint, vulnerable, sampled }] }
GET  /api/queue?client_id=           → [{ call_id, agent_name, kind, risk_tier, reason, confidence, due_at }]
POST /api/calls/{id}/evaluation      { items:[{ id, answer, reason }], comments }
                                     → { evaluation, corrections:[{ item_id, before, after, reason }], rules:[{ id, text }], playbook_version }
POST /api/rules/{id}/test            → { changed:[{ call_id, item_id, before, after }] }               (test on archive)
GET  /api/clients/{id}/agreement     → { overall_pct, by_item:[{ item_id, label, pct, n, auto_accept }], history:[{ date, pct }] }
GET  /api/reports/{client_id}/draft  → { id, period, status, sections:[{ id, kind:"summary"|"finding"|"vulnerable"|"complaints"|"coaching"|"actions",
                                         title, body, evidence_call_ids:[id], version }] }
POST /api/reports/sections/{id}      { body, reason } → { section, rule }
POST /api/reports/{id}/send          → { sent:true, to, message_id }
POST /api/escalations/{call_id}/send → { sent:true, to, message_id }
GET  /api/learning?client_id=        → { review:{ version, rules:[{ id, text, from_call, created_at }] },
                                         report:{ version, rules:[...] }, corrections:[...] }
GET  /api/compare?client_id=         → { runs:[{ label:"base"|"playbook"|"adapter", metrics:{ item_accuracy, critical_recall,
                                         complaint_recall, vulnerability_recall, latency_p50_ms, cost_per_1k_calls_gbp },
                                         per_call:[{ call_id, correct }] }] }
GET  /api/traces?limit=50            → [{ ts, task, request_id, model, latency_ms, record }]
POST /api/demo/reset
```

---

## 6. Screens (for the UI session; style is its call)

| Screen | Content | Copied from |
|---|---|---|
| **Wall** | 100 tiles, one per call this week. "Contract samples 2" lights 2; then all 100 flip to their risk colour. Stats underneath. | ContactBabel's 1–2%; Recordsure's under 5% → 100% |
| **Queue** | Escalate now · analyst · audit, each with risk tier, reason and due time | EvaluAgent AutoWorkQueues; Aveni risk-ranked queue |
| **Evaluation form** | The pre-filled scorecard: AI answer, quote with ▶ timestamp, rule, confidence → ✓ or change + reason. Critical fails pinned. Live total. Comments. Submit. | EvaluAgent scorecard; Recordsure evidence links |
| **Agreement** | AI vs analyst agreement per item, plus a trend line; auto-accept badges | EvaluAgent calibration reports; Recordsure's 95% agreement |
| **Report editor** | Sections with evidence links. Edit + reason → rule. Send. | Recordsure client reports; FCA board report good practice |
| **Learning** | Rules per client and task, playbook versions, "test on archive" results | EvaluAgent testing console; Aveni overrides with reasons |
| **Mubit panel** | Every model call: task, request ID, model, latency, record mode; links to Tasks and Try models | — |

---

## 7. Demo data
- **Harbour Assurance** (the QA firm) and its clients **Thistle Bank** and **Northwind Finance**. All fictional.
- **Thistle: 100 synthetic call transcripts.**
  - **About 40% are hard cases**: hidden complaints, vulnerability mentioned in passing, wrong deadline, a promised refund, a skipped identity check.
  - 75 practice calls (Mubit warm-up, the wall, corrections) · 25 held-out calls (`metadata`, gold labels written **before** any run).
- **Northwind:** 12–20 calls (its task stays partly trained, on purpose).
- **Live call:** the scripted role-play in [CALLING.md](CALLING.md).
- All calls go through Mubit. Generating the synthetic transcripts can also use Mubit, as a separate `data.generate` task.
