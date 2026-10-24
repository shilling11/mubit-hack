# Redline — RFP responses that learn from every correction

> **Night Shift: $65K Mubit Hackathon, London** · 23–25 October 2026
> Event page: <https://luma.com/nightshift-london>
>
> **One-liner:** Every LLM call in the bid workflow goes through Mubit. When a bid manager fixes a draft, Mubit turns the fix into a model update, so the next RFP's first draft is already better.

---

## 0. How to use this README (for Claude / coding agents)

This file is the **single source of truth** for building the repo. When prompting Claude:

- Build in the order in [§9 Build Plan](#9-build-plan-ruthlessly-prioritised). Don't start P2 work until the P0 golden path runs end to end.
- **Hard rule: every LLM call in the app goes through the Mubit client (`app/llm/mubit_client.py`).** Don't add direct OpenAI/Anthropic calls anywhere else.
- The Mubit integration in §3 was verified against <https://docs.mubit.ai> and live calls on 24 Oct 2026. Anything still marked `TODO(mubit)` needs confirming with the Mubit team. **Don't invent Mubit endpoints, SDK methods or parameters.**
- All data is **synthetic**. Never add real client, Accenture or third-party RFP content to this repo.

---

## 1. Problem overview and narrative

### The problem
Consulting firms, systems integrators and SaaS vendors answer hundreds of RFPs a year. Every RFP comes as a **package**: a narrative Word/PDF document plus Excel exhibits (requirements matrix, security questionnaire, pricing, plan, risks, clarifications).

Each row of the requirements and security tabs asks for the same thing:

> *Read the requirement → decide Comply / Partially Comply / Do Not Comply → write a defensible response → cite evidence → flag gaps.*

That's a **recurring task**, done thousands of times a year by expensive people. Today's options:

| Option | Failure mode |
|---|---|
| Humans copy-paste from old bids | Slow, inconsistent, outdated answers |
| Generic LLM / company chatbot | Fluent but over-confident. It says "Fully comply" to things the company can't deliver |
| Content-library tools | Retrieve old text but don't learn the bid team's judgement |

The most expensive failure is **an unsupported commitment** made in a binding bid. For example, the bid claims 99.99% availability when the company's standard service is 99.9%.

### The insight
Bid managers already **correct** AI drafts all day. Those corrections hold the organisation's real judgement:

- "We never claim full compliance on SLAs above our managed-service standard."
- "Data residency answers must name the UK region and cite the security policy."
- "Pricing assumptions must reference the volumes tab."

Today those corrections are lost once the bid ships.

### The solution
**Redline** is a company bid agent that sends **every LLM call through Mubit**. Each correction a bid manager makes is captured as feedback, and **Mubit turns it into a lightweight model update** for the recurring task. Next time, the first draft already reflects the team's judgement. The base model stays fixed and only the task-specific update refreshes.

### Narrative for the judges (30-second version)
> "RFPs are the same task repeated thousands of times. Generic agents write fluent answers that over-promise. We route every call through Mubit. When our bid manager corrects the agent on RFP #1, Mubit turns that correction into a model update, and on a brand-new RFP the agent gets it right first time. It's cheaper and faster too, because it runs on a task-adapted open model."

**Money line:** *Without Mubit, the agent drafts. With Mubit, the agent learns how **your** company bids.*

---

## 2. Hackathon info

| Item | Detail |
|---|---|
| Event | Night Shift: $65K Mubit Hackathon in London |
| Link | <https://luma.com/nightshift-london> |
| Format | 42-hour overnight hackathon, around 500 builders |
| Dates | Fri 23 Oct 2026, 17:00 → Sun 25 Oct 2026, 14:00 (clocks go back on Sunday, so there's an extra hour) |
| Prizes | 1st $15,000 · 2nd $10,000 · 3rd $5,000 · $35,000 in AI credits · $1.5M in Mubit credits for accepted hackers |

### The brief
Build a product that **routes its LLM calls through Mubit** (one base URL change) and **turns your corrections into model updates for a recurring task**.

### Tracks (top 3 prizes judged across all tracks)
1. **Recurring tasks** – a task run again and again (extraction, triage, support replies, review, routing). Show corrections becoming model updates. ← **our primary track**
2. **Own your intelligence layer** – move a closed-model workload onto a task-adapted open model. Show quality, cost and latency side by side. ← **we show this as a panel**
3. **Fast refresh** – a workload that keeps changing. Show model updates keeping pace. ← **we show this with a second client/domain RFP**

### Judging (four criteria, weighted equally)
| Criterion | How Redline scores |
|---|---|
| **Use of Mubit** – show a correction turning into a model update | Live correction on RFP #1 → model update → improved draft on unseen RFP #2. Every call is visibly routed through Mubit |
| **Usefulness** – a real recurring task | RFP requirement responses are a high-volume, high-cost, high-risk recurring task in consulting and enterprise sales |
| **Technical execution** – works and holds up under questions | Deterministic parsing, structured JSON outputs, held-out eval set, before/after metrics, no hard-coded results |
| **Demo** – clear, live, under the time limit | 3-minute scripted golden path (see §8) |

### Key schedule
| When | What |
|---|---|
| Fri 19:30 | Hacking starts |
| Sat all day | Office hours with the Mubit team. **Use them to confirm API and feedback/update mechanics** |
| **Sun 10:00** | **Code freeze, submissions close** |
| Sun 10:30 | Judging round 1 (expo) |
| Sun 12:30 | Finalist demos on stage |
| Sun 13:30 | Awards |

---

## 3. How Mubit is used throughout

Mubit sits **between Redline and every model call**. Nothing calls a model directly: `app/llm/mubit_client.py` is the only module that does.

```text
                ┌────────────────────────────────────────────┐
  RFP package → │                Redline app                 │
 (DOCX + XLSX)  │  Ingest (no LLM) → Retrieve (BM25, no LLM) │
                │  Extract · Draft · Verify · Induce · Summ. │
                │                     ▼                      │
                │          app/llm/mubit_client.py           │
                └─────────────────────┬──────────────────────┘
                                      ▼  OpenAI-compatible, one base-URL change
                    ┌──────────────────────────────────┐
                    │  MUBIT  api.mubit.ai/openai/v1   │
                    │  records calls · groups tasks    │
                    │  keeps examples · trains adapter │
                    │  routes to a passing adapter     │
                    └────────────────┬─────────────────┘
                                     ▼
                     Provider model (starter credit) or task adapter
```

### What Mubit actually does (verified)

| Fact | How Redline uses it |
|---|---|
| Base URL `https://api.mubit.ai/openai/v1`, Mubit key (`mbt_…`) as the API key | `MUBIT_BASE_URL`, `MUBIT_API_KEY` in `.env` |
| A **task** is the set of calls sharing model + system prompt + tools + output format. There is no task-tag parameter | One fixed system prompt (`app/llm/prompts/*.md`) and one JSON schema per task. Everything that varies (requirement, evidence, playbook) goes in the **user** message |
| Every answer carries `x-middleware-request-id` (`mreq_…`); `response.model` shows what served it | Logged per call in SQLite and shown in the trace panel |
| `x-middleware-record: full / metadata / off` controls what Mubit keeps | Base (v0) runs use `metadata`, so the uncorrected answers never become training examples |
| Mubit trains an **adapter** for a task once it has 25 kept examples, tests it against the provider model, and (per the Mubit team) routes to a passing version | `scripts/warm_mubit.py` sends corrected-behaviour calls to reach the threshold; the trace panel highlights calls served by a model other than the one asked |
| `metadata.session_id` needs OpenAI `store=true` | Not sent. We don't want OpenAI storing calls |
| The Mubit docs describe **no feedback/correction API**. `mubit-sdk` (`remember`, `record_outcome`) exists on PyPI but its endpoints returned `unknown_route` on our gateway key | Corrections are captured by Redline (below). `TODO(mubit)`: ask whether a memory/outcome endpoint is available for our project |
| Starter credit serves: gpt-6-sol, gpt-6.1-sol, gpt-6-luna, gpt-6-astra, gpt-5.5, gpt-4o-mini, gpt-4.1-mini; claude-opus-5-5, claude-sonnet-5-5, claude-haiku-4-5 | `MUBIT_MODEL` / `BASELINE_MODEL` |

### Every pipeline stage goes through Mubit

| Stage | Mubit task (system prompt) | Module |
|---|---|---|
| Extract implicit requirements from DOCX prose | `rfp.extract_requirements` | `app/pipeline/extract.py` |
| **Draft status + response per requirement** | **`rfp.draft_response`** (core task) | `app/pipeline/draft.py` |
| Verify claims against evidence | `rfp.verify_claims` | `app/pipeline/verify.py` |
| Turn a correction into a reusable rule | `rfp.induce_rule` | `app/learning/playbook.py` |
| Executive summary + win risks | `rfp.exec_summary` | `app/pipeline/summarise.py` |

File/tab classification and SME routing are done with plain code (no LLM), because the workbook structure is fixed.

### The correction → model update loop

```text
 Draft v0 (Mubit, not trained on) → Bid manager corrects + gives a reason → Correction record
        ▲                                                                       │
        │                                                       rfp.induce_rule (Mubit)
        │                                                                       ▼
 Draft on unseen RFP with playbook vN  ←────────── Playbook vN: generalised rules + worked examples
        │
        └─► corrected-behaviour calls = Mubit kept examples → adapter trains (25) → Mubit routes to it
```

1. **Immediate update.** Building a playbook version induces one generalised rule per correction through Mubit. Draft calls carry the playbook in the user message, so the next RFP's first draft changes straight away, on the same Mubit task.
2. **Model update.** Those corrected calls are kept examples for `rfp.draft_response`. Mubit trains a task adapter from them, so a cheap open model learns the team's judgement. Before the demo, run `python -m scripts.warm_mubit` and check the Mubit console (Tasks → Adapters).

A **correction record** (SQLite `corrections` table):
```json
{
  "req_id": "S-001", "package": "northstar", "run_id": "run_…", "request_id": "mreq_…",
  "requirement": "...",
  "model_output": {"status": "Partially Comply", "response": "...", "evidence_ids": ["..."], "gaps": "..."},
  "corrected_output": {"status": "Comply", "response": "...", "evidence_ids": ["..."], "gaps": ""},
  "correction_type": ["status_change"],
  "rationale": "We meet this with the standard service: answer Comply and put ordinary qualifiers in the response.",
  "rule": {"rule": "...", "applies_when": "...", "keywords": ["..."]}
}
```

**Never fake the after result.** Every number on the Compare tab comes from real Mubit calls scored against hand-written gold labels, with no LLM judge.

---

## 4. Synthetic data

All data is fictional and safe to publish.

| File | Role | Status |
|---|---|---|
| `data/rfps/northstar/*.docx + *.xlsx` | RFP #1 (retail), 24 requirements + 12 security questions, including the 4 trap rows | ✅ |
| `data/rfps/meridian/*.docx + *.xlsx` | **RFP #2, held out** (health insurer), 18 requirements + 8 security questions | ✅ generated |
| `data/rfps/kestrel/*.docx + *.xlsx` | RFP #3 (county council), practice/warm-up + fast refresh | ✅ generated |
| `data/company_kb/*.md` | Fictional supplier **Ashgrove Digital**: capabilities, SLA standard (**99.9%**), security, data protection, AI governance, pricing guardrails, integrations, delivery, case studies, SMEs (48 passages) | ✅ |
| `data/corrections/seed.jsonl` | 2 pre-recorded corrections (AI-004, C-003) | ✅ |
| `data/eval/gold_*.jsonl` | Hand-written gold labels for all three RFPs: status (+ acceptable alternatives), trap flag, key facts, valid evidence | ✅ |

`python scripts/generate_synthetic.py` rebuilds the Meridian and Kestrel packages and adds the Northstar trap rows (safe to re-run).

### Deliberate traps (these make the demo work)
Add these rows to the RFP #1 Requirements tab, with matching rows in RFP #2:

| ID | RFP #1 requirement | KB truth | Correct answer | RFP #2 variant |
|---|---|---|---|---|
| S-003 | 99.99% monthly availability | Standard is 99.9% | Partially Comply + gap | "Four-nines uptime for member portal" |
| D-003 | Data must never leave the UK, including support access | Follow-the-sun support from India | Partially Comply + mitigation | "No offshore access to patient data" |
| AI-004 | Fully autonomous refunds of any value | Human approval above threshold | Do Not Comply (by design) | "Auto-approve claims without review" |
| C-003 | Fixed price for unlimited use cases | Pricing guardrail forbids it | Partially Comply + assumption | "Fixed fee, uncapped scope" |

The base model will tend to say "Comply" to these. The corrections teach the company's rules. RFP #2 tests whether the rules **generalise** to new wording and domains, rather than being memorised.

---

## 5. Features to add

### P0 – Golden path (must ship)
1. **RFP package upload** – drag in one DOCX and one XLSX; detect the shared RFP reference.
2. **Deterministic parsing** – `python-docx` for sections, `openpyxl` for tabs and rows (requirement IDs come straight from the sheet; no LLM needed for the table).
3. **Requirement extraction via Mubit** – pull extra implicit requirements from DOCX prose (`rfp.extract_requirements`).
4. **Evidence retrieval** (our own layer) – BM25 or embeddings over `data/company_kb`; top-k passages per requirement, passed into the Mubit call.
5. **Draft responses via Mubit** (`rfp.draft_response`) – strict JSON: `status`, `response`, `evidence_ids`, `gaps`, `confidence`.
6. **Correction UI** – edit status/response inline, add a rationale, click **"Teach"** → `submit_correction()` sends it to Mubit.
7. **Model update + re-run** – trigger/poll the Mubit update; re-run RFP #2 with the updated task model.
8. **Before/after scoreboard** – accuracy on held-out RFP #2 (status match, unsupported-claim count, citation coverage), from real runs.
9. **Mubit trace panel** – every call listed with task, request ID, model/update version, latency and tokens.

### P1 – Makes it a winner
10. **Quality / cost / latency comparison** – the same RFP #2 run on a closed frontier model vs the Mubit task-adapted open model (Track 2).
11. **Over-promise detector** (`rfp.verify_claims`) – red-flags any "Comply" without supporting evidence.
12. **Correction analytics** – correction types over time, plus "corrections per bid" trending down.
13. **Update timeline** – v0 → v1 → v2 of the task update, with the corrections that went into each.
14. **Export** – write the completed Requirements and Security tabs back into the XLSX, plus a DOCX response pack.

### P2 – Nice to have
15. **SME routing** (`rfp.route_owner`) from the fictional SME directory.
16. **Win-risk summary** – "What are we most likely to lose this bid on?"
17. **Fast-refresh demo** – a third domain RFP and a quick update cycle (Track 3).
18. **Evidence graph view** – requirement → KB passage → past project → SME.

### Explicitly out of scope
Real client data · authentication · multi-tenant · full proposal-management workflow · fine-tuning outside Mubit.

---

## 6. Architecture and repo layout

```text
mubit-hack/
├── README.md
├── .env.example              # MUBIT_BASE_URL, MUBIT_API_KEY, MUBIT_MODEL, BASELINE_MODEL
├── requirements.txt
├── app/
│   ├── main.py               # FastAPI entrypoint (all /api routes)
│   ├── config.py · db.py · models.py
│   ├── llm/
│   │   ├── mubit_client.py   # ONLY model gateway: call() + trace logging
│   │   └── prompts/          # one fixed system prompt per Mubit task
│   ├── ingest/               # docx_parser.py, xlsx_parser.py, packages.py (registry + gold)
│   ├── pipeline/             # retrieve.py (BM25), draft.py, verify.py, extract.py, summarise.py, runner.py
│   ├── learning/             # corrections.py, playbook.py (versioned rules via rfp.induce_rule)
│   ├── eval/score.py         # deterministic scoring vs gold
│   └── export/writeback.py   # fill the client XLSX
├── web/                      # Next.js 16 + Tailwind 4 (Overview, Matrix, Learning, Compare, trace panel)
├── data/                     # synthetic only (see §4)
└── scripts/
    ├── generate_synthetic.py # build RFP packages
    ├── run_eval.py           # CLI scoreboard: base vs latest playbook
    ├── warm_mubit.py         # send corrected calls so Mubit trains the adapter
    └── reset_demo.py         # clear runs/corrections/traces
```

**Stack:** Python 3.11, FastAPI, Pydantic, python-docx, openpyxl, rank-bm25, SQLite (`redline.db`) for runs, corrections and traces; Next.js 16, Tailwind 4, lucide-react.

**Data model (Pydantic):** `Requirement`, `Evidence`, `Draft`, `Correction`, `MubitTrace`, `EvalResult`.

---

## 7. UI/UX

**Design principle:** the audience should *see* learning happen. Every screen shows the Mubit update version.

### Layout
```text
┌──────────────────────────────────────────────────────────────────────┐
│ Redline   RFP: NSR-2026-AI-014 ▾      Mubit ● task update v1  ⓘ      │
├────────────┬──────────────────────────────────────┬──────────────────┤
│ Package    │  REQUIREMENTS MATRIX                 │  MUBIT PANEL     │
│ ▸ RFP.docx │  ID     Status        Conf  Evidence │  Live traces     │
│ ▸ Exhibits │  F-001  ● Comply      0.94  3        │  draft_response  │
│            │  S-003  ● Partial ⚠   0.88  2        │  412ms · v1      │
│ Tabs       │  D-003  ● Partial     0.81  2        │  …               │
│ Overview   │  …                                   │  Corrections: 7  │
│ Matrix     │                                      │  Update: v0→v1 ✓ │
│ Learning   │  [ Selected row: draft | evidence |  │  [Teach Mubit]   │
│ Compare    │    edit + rationale | Teach ▶ ]      │                  │
└────────────┴──────────────────────────────────────┴──────────────────┘
```

### Screens
1. **Overview** – requirement count, status split (🟢 / 🟡 / 🔴), evidence coverage, flagged over-promises.
2. **Matrix** – sortable table. Click a row to open the drawer with the draft, cited evidence (click to view the passage), an edit box, a rationale field and the **Teach** button.
3. **Learning** – correction feed, update timeline (v0 → v1), "what changed" per correction type.
4. **Compare** – side-by-side on held-out RFP #2:
   - Left: **Base (no update)**. Right: **Mubit task update**.
   - Scores: status accuracy, unsupported claims, citation coverage.
   - Cost per RFP, latency p50, closed model vs Mubit open model.

### Micro-interactions that sell it
- **Teach** button → toast "Correction sent to Mubit" → update badge pulses "building…" → "v1 ready".
- Changed rows on re-run get a highlight, with a diff of old vs new status.
- Trap rows show a red shield icon when the base model over-promises, and turn green after the update.

---

## 8. Demo script (3 minutes, live)

| Time | Beat | On screen |
|---|---|---|
| 0:00–0:20 | **Problem.** "Every RFP is the same task, repeated thousands of times. Generic agents over-promise." | Title + RFP package |
| 0:20–0:50 | **Upload RFP #1.** Parse DOCX + XLSX. Drafts stream in. Mubit trace panel fills: every call goes through Mubit. | Matrix + traces |
| 0:50–1:20 | **The trap.** S-003 99.99% → base model says "Comply". "That's a contractual commitment we can't meet." | Red shield on S-003 |
| 1:20–1:50 | **Correct it.** Change to Partially Comply, cite the 99.9% SLA standard, add a rationale, **Teach**. Fix one or two more (D-003). | Correction → Mubit |
| 1:50–2:10 | **Model update.** Mubit update v0 → v1 (live, or pre-built with its version/timestamp shown). | Learning tab |
| 2:10–2:40 | **Unseen RFP #2** (health insurer, different wording). Base vs v1 side by side: four-nines and offshore-access traps are now handled correctly. | Compare tab |
| 2:40–3:00 | **Scoreboard + money line.** Held-out accuracy up, unsupported claims down, cost and latency vs the closed model. "Without Mubit, the agent drafts. With Mubit, it learns how your company bids." | Scoreboard |

**Backup plan:** a recorded video of the golden path, plus a cached run of RFP #2 (labelled as cached) in case venue Wi-Fi fails.

**Likely judge questions – prepare answers for:**
- *Isn't this just RAG?* → Retrieval supplies the facts. Mubit learns the **judgement**: when to say Partial, how to phrase gaps and what never to claim. RFP #2 shows that judgement generalising to new wording.
- *Did you overfit to the demo?* → RFP #2 is held out, from a different domain and with different wording. The gold labels were written before training.
- *Why open models?* → Cost and latency per RFP at scale, shown on the Compare tab. The company also owns its bid-judgement layer.
- *Real data?* → Synthetic only. In a real firm, corrections are generated naturally in every bid review.

---

## 9. Build plan (ruthlessly prioritised)

| Order | Task | Status |
|---|---|---|
| 1 | Confirm the Mubit API | ✅ verified (§3); feedback API still `TODO(mubit)` |
| 2 | Parsers for DOCX + XLSX | ✅ |
| 3 | Synthetic KB + trap rows + RFP #2/#3 + gold labels | ✅ |
| 4 | `draft_response` via Mubit with strict JSON + retrieval | ✅ |
| 5 | Correction capture + playbook versions | ✅ |
| 6 | Re-run on RFP #2 + scoring | ✅ |
| 7 | UI: Overview, Matrix + Teach, Learning, Compare | ✅ built; needs a click-through in the browser |
| 8 | Trace panel + model comparison | ✅ (closed-baseline run button on Compare) |
| 9 | Warm Mubit to 25 kept examples, confirm adapter + "Served by" | 🔲 run `scripts/warm_mubit.py`, check console |
| 10 | Decide demo narrative (§12), polish, record backup video, rehearse | 🔲 **before Sun 10:00 code freeze** |

---

## 10. Setup

```powershell
# Backend (Python 3.11+)
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env          # set MUBIT_API_KEY (mbt_…)
.\.venv\Scripts\python -m uvicorn app.main:app --port 8000   # no --reload when demoing: a reload kills in-flight runs

# Frontend (from PowerShell)
cd web; npm install; npm run dev   # http://localhost:3000

# Optional
.\.venv\Scripts\python scripts\generate_synthetic.py
.\.venv\Scripts\python -m scripts.run_eval --rfp meridian --compare base,latest
.\.venv\Scripts\python -m scripts.warm_mubit
.\.venv\Scripts\python -m scripts.reset_demo
```

---

## 11. Ethics and data

- 100% synthetic organisations, people, numbers and documents.
- No real RFPs or internal company material in the repo, prompts, demo or screenshots.
- Human-in-the-loop by design: the agent drafts and flags; a bid manager approves.

---

## 12. Findings so far (real runs, 24 Oct 2026)

Held-out Meridian pack, 26 rows, one run per cell, scored against the gold labels:

| Model | Base v0 | Playbook v1 (4 corrections) |
|---|---|---|
| gpt-6-luna | 84.6% status accuracy, 0 over-promises, 4 hedged | **92.3%** |
| gpt-4o-mini | 92.3% | 88.5% |
| gpt-4.1-mini | 92.3% (1 over-promise) | not run |

- Grounded in a clean knowledge base, current models rarely **over-promise**: `gpt-6-luna` got all four trap rows right with no playbook. Its main failure is **under-claiming**: answering "Partially Comply" to requirements the company fully meets. On a mandatory row that can eliminate the bid (Northstar §8).
- Two hedging corrections on Northstar fixed hedging on *different* Meridian rows (REQ-01, REQ-16, SEC-07): real generalisation. The strict seed rules (AI-004, C-003) nudged some partials to "Do Not Comply", which the scoreboard catches.
- n is small and runs vary by a row or two, so rehearse with the numbers from the day.
- **Decision needed:** pitch "calibration" (agents both over-promise and hedge; corrections teach the team's judgement both ways) rather than the pure over-promise story in §1 and §8.
