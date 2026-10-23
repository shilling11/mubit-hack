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
- Every Mubit integration detail marked `TODO(mubit)` must be confirmed against the Mubit docs or kickoff walkthrough. **Don't invent Mubit endpoints, SDK methods or parameters.**
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

Mubit sits **between Redline and every model call**. Nothing calls a model directly.

```text
                ┌────────────────────────────────────────────┐
  RFP package → │                Redline app                 │
 (DOCX + XLSX)  │                                            │
                │  1 Ingest  2 Extract  3 Draft  4 Verify   │
                │      │         │         │         │       │
                │      └─────────┴────┬────┴─────────┘       │
                │                     ▼                      │
                │          app/llm/mubit_client.py           │
                └─────────────────────┬──────────────────────┘
                                      ▼
                    ┌──────────────────────────────────┐
                    │              MUBIT               │
                    │  routes calls · logs traces      │
                    │  ingests corrections/feedback    │
                    │  builds lightweight model updates│
                    └────────────────┬─────────────────┘
                                     ▼
                     Fixed base open model + task update
                                     ▲
  Bid manager edits ─── corrections ─┘  (the learning loop)
```

### Every pipeline stage goes through Mubit

| # | Stage | Mubit task name | Recurring? | Learns from corrections? |
|---|---|---|---|---|
| 1 | Classify the uploaded file and tab types | `rfp.classify_artifact` | Yes | Light |
| 2 | Extract structured requirements from DOCX prose | `rfp.extract_requirements` | Yes | Yes (missed or merged requirements) |
| 3 | **Draft compliance status + response per requirement** | `rfp.draft_response` | **Yes – core task** | **Yes – the main demo** |
| 4 | Verify claims against evidence and flag over-promising | `rfp.verify_claims` | Yes | Yes |
| 5 | Route requirements to the right SME/owner | `rfp.route_owner` | Yes | Yes |
| 6 | Write the executive summary and win-risk analysis | `rfp.exec_summary` | Yes | Light |

**Demo focus:** stage 3 (`rfp.draft_response`) is the task where we show corrections becoming a model update. The other stages still route through Mubit, so the trace view shows Mubit is used everywhere.

### The correction → model update loop (core of the demo)

```text
 Draft (Mubit)  →  Bid manager edits  →  Correction record  →  Mubit feedback
       ▲                                                          │
       │                                                          ▼
 Better draft on new RFP  ←  task-adapted model  ←  Mubit model update
```

A **correction record** contains:
```json
{
  "task": "rfp.draft_response",
  "request_id": "<Mubit trace/request id>",
  "requirement_id": "S-003",
  "input": {"requirement": "...", "evidence": ["..."]},
  "model_output": {"status": "Comply", "response": "..."},
  "corrected_output": {"status": "Partially Comply", "response": "...", "gap": "..."},
  "correction_type": ["status_change", "unsupported_claim_removed", "citation_added"],
  "rationale": "Managed-service standard is 99.9%; never claim 99.99% without service-owner approval.",
  "editor": "demo-bid-manager",
  "timestamp": "..."
}
```

### Integration contract (confirm at kickoff)

```python
# app/llm/mubit_client.py — the ONLY module allowed to call a model
# TODO(mubit): confirm base URL, auth header, model naming, and the
#              feedback/correction + model-update APIs from Mubit docs.
import os
from openai import OpenAI  # Mubit is described as a one-base-URL-change integration

client = OpenAI(
    base_url=os.environ["MUBIT_BASE_URL"],   # TODO(mubit)
    api_key=os.environ["MUBIT_API_KEY"],     # TODO(mubit)
)

def call(task: str, messages: list, schema: dict | None = None, **kw) -> dict:
    """Route an LLM call through Mubit. Tag it with `task` so updates are per-task.
    Returns {output, request_id, latency_ms, tokens, model}."""
    ...

def submit_correction(record: dict) -> None:
    """Send a correction to Mubit as feedback for `record['task']`.  TODO(mubit)"""
    ...

def trigger_update(task: str) -> str:
    """Ask Mubit to build/refresh the model update for a task (if manual). TODO(mubit)"""
    ...

def update_status(task: str) -> dict:
    """Poll update status/version for the UI badge. TODO(mubit)"""
    ...
```

**Fallback if model updates take longer than the demo slot:** pre-run the update before going on stage, and show (a) the correction being submitted live, (b) the update version/timestamp in Mubit, and (c) the before/after on the held-out RFP. **Never fake the after result.** Everything shown must come from real Mubit calls.

---

## 4. Synthetic data

All data is fictional and safe to publish.

| File | Role | Status |
|---|---|---|
| `data/rfps/northstar/Northstar_Retail_AI_Transformation_RFP.docx` | RFP #1 narrative (retail, AI customer operations) | ✅ exists |
| `data/rfps/northstar/Northstar_Retail_RFP_Exhibits.xlsx` | RFP #1 exhibits, 9 tabs: Read Me, Requirements, Security Questionnaire, Pricing, Volumes & Assumptions, Implementation Plan, Risks & Assumptions, Clarifications, Evaluation | ✅ exists |
| `data/rfps/meridian/…docx + …xlsx` | **RFP #2 – held-out** (e.g. Meridian Health / insurer). Different domain, and it includes requirements that are *similar but not identical* to the corrected ones | 🔲 to generate |
| `data/rfps/kestrel/…` | RFP #3 for "fast refresh" (e.g. public sector / new domain) | 🔲 optional |
| `data/company_kb/*.md` | Fictional internal knowledge: capability statements, security policy, managed-service SLA standard (**99.9%**), 4 past case studies, AI governance standard, pricing guardrails, SME directory | 🔲 to generate |
| `data/corrections/seed.jsonl` | Pre-recorded bid manager corrections for warm-up | 🔲 to generate |
| `data/eval/gold_*.jsonl` | Gold answers for each requirement in RFP #2 (status + key facts) | 🔲 to generate |

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
redline/
├── README.md
├── .env.example              # MUBIT_BASE_URL, MUBIT_API_KEY, MUBIT_MODEL, BASELINE_MODEL
├── requirements.txt
├── app/
│   ├── main.py               # FastAPI entrypoint
│   ├── llm/
│   │   ├── mubit_client.py   # ONLY model gateway (call/submit_correction/trigger_update/update_status)
│   │   └── prompts/          # one prompt file per Mubit task
│   ├── ingest/
│   │   ├── docx_parser.py
│   │   └── xlsx_parser.py
│   ├── pipeline/
│   │   ├── extract.py        # rfp.extract_requirements
│   │   ├── retrieve.py       # KB retrieval (no LLM)
│   │   ├── draft.py          # rfp.draft_response
│   │   ├── verify.py         # rfp.verify_claims
│   │   └── summarise.py      # rfp.exec_summary
│   ├── learning/
│   │   ├── corrections.py    # store + send corrections to Mubit
│   │   └── updates.py        # trigger/poll Mubit updates
│   ├── eval/
│   │   └── score.py          # held-out scoring vs gold
│   └── export/
│       └── writeback.py      # fill XLSX + build DOCX
├── web/                      # Next.js + Tailwind + shadcn/ui (or Streamlit fallback)
├── data/                     # synthetic only (see §4)
└── scripts/
    ├── generate_synthetic.py
    ├── seed_corrections.py
    └── run_eval.py
```

**Stack:** Python 3.11, FastAPI, Pydantic, python-docx, openpyxl, rank-bm25 (or a small embedding model), SQLite for corrections/traces, Next.js + Tailwind + shadcn/ui. **Fallback UI:** Streamlit if time runs short. A working demo beats a pretty, broken one.

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

| Order | Task | Done when |
|---|---|---|
| 1 | Confirm the Mubit API at office hours: base URL, auth, task tagging, feedback API, update trigger/latency | `mubit_client.call()` returns real output |
| 2 | Parsers for the existing Northstar DOCX + XLSX | Requirements JSON printed |
| 3 | Generate the synthetic KB + trap rows + RFP #2 + gold labels | `data/` complete |
| 4 | `draft_response` via Mubit with strict JSON + retrieval | Matrix filled for RFP #1 |
| 5 | Correction capture + `submit_correction` | Corrections visible in Mubit |
| 6 | Update + re-run on RFP #2 + scoring | Real before/after numbers |
| 7 | Minimal UI: Matrix, Teach, Compare | Golden path clickable |
| 8 | Trace panel + cost/latency comparison | Track 2 evidence |
| 9 | Polish, record backup video, rehearse under 3 minutes | **Before Sun 10:00 code freeze** |

---

## 10. Setup

```bash
git clone <repo> && cd redline
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill MUBIT_BASE_URL, MUBIT_API_KEY (TODO(mubit))
python scripts/generate_synthetic.py
uvicorn app.main:app --reload
cd web && npm install && npm run dev
python scripts/run_eval.py --rfp meridian --compare base,mubit
```

---

## 11. Ethics and data

- 100% synthetic organisations, people, numbers and documents.
- No real RFPs or internal company material in the repo, prompts, demo or screenshots.
- Human-in-the-loop by design: the agent drafts and flags; a bid manager approves.
