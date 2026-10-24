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
| Mubit trains an **adapter** for a task once it has 25 kept examples, and grades each version on how closely it matches the provider model's answers. **Adapters have no model ID and can't be called by API: they run only in the console's Try models** (confirmed by the Mubit team) | `scripts/warm_mubit.py` sends corrected-behaviour calls to reach the threshold. The adapter copies the provider *on our inputs*, which include the playbook, so it learns the corrected behaviour. Shown live in Try models, not in our app |
| `metadata.session_id` needs OpenAI `store=true` | Not sent. We don't want OpenAI storing calls |
| **Corrections are made in the Mubit console; there is no API for them.** A Bad rating doesn't remove a call from training; `x-middleware-record: metadata` does (Mubit team). `mubit-sdk` endpoints returned `unknown_route` on our key | Redline captures corrections itself and turns them into playbook rules. Base and held-out runs are sent with `metadata`, so they never train the adapter |
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
2. **Model update.** Those corrected calls are kept examples for `rfp.draft_response`. Mubit trains a task adapter from them, so a cheap open model learns the team's judgement. The app can't call or retrain the adapter directly (no API); it changes through these calls. Before the demo, run `python -m scripts.warm_mubit` and check the Mubit console (Tasks → Adapters), then show the adapter in Try models.

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
| `data/rfps/meridian/*.docx + *.xlsx` | Health insurer, 18 requirements + 8 security questions. Practice (was the held-out pack until its calls were sent to Mubit for training on 24 Oct) | ✅ generated |
| `data/rfps/kestrel/*.docx + *.xlsx` | County council, practice/warm-up + fast refresh | ✅ generated |
| `data/rfps/orbis/*.docx + *.xlsx` | Energy supplier, 30 requirements + 6 security questions, practice/warm-up (no gold) | ✅ generated |
| `data/rfps/thistle/*.docx + *.xlsx` | **Held out** (retail bank), 18 requirements + 8 security questions. Every run on it is recorded as `metadata`, so Mubit never trains on it (`REDLINE_HELD_OUT`) | ✅ generated |
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

**Design principle:** the audience should *see* learning happen. Editorial "red pen" look: paper and ink, with red reserved for corrections and risk.

### Layout
```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Redline   RFP: NSR-2026-AI-014 ▾                     Mubit ● playbook v1     │
├──────────────────────────────────────────────────────────────────────────────┤
│ ① Upload ✓ ─ ② Draft ✓ ─ ③ Correct [Review matrix] ─ ④ Learn ─ ⑤ Prove       │  ← demo rail
├────────────┬───────────────────────────────────────────┬─────────────────────┤
│ Overview   │  REQUIREMENTS MATRIX                      │  MUBIT GATEWAY      │
│ Document   │  ID     Status     Conf  Evid  Risk       │  calls · errors     │
│ Matrix     │  S-001  Partial    0.62  2     unsure     │  live traces:       │
│ Learning   │  S-003  Partial    0.99  2                │  draft_response     │
│ Compare    │  …                         [row drawer ▶] │  mreq_… · 4.1s      │
└────────────┴───────────────────────────────────────────┴─────────────────────┘
```

### Screens
1. **Demo rail** (always visible): ① Upload ② Draft ③ Correct ④ Learn ⑤ Prove. The current step glows red and has one big button. Clicking a step's label only navigates.
2. **Overview:** upload a DOCX + XLSX pair, draft with Mubit, status split, over-promise flags, low-confidence count, narrative extraction, executive summary, **Open completed workbook** (exports and opens the filled XLSX in Excel).
3. **Document:** the RFP narrative, section by section, with a contents list.
4. **Matrix:** every requirement with status, confidence, evidence and the over-promise detector (no gold labels here). The row drawer shows the draft, its evidence, **Verify claims**, and the correction form with live **tracked changes**, plus **Teach** and **Teach & ripple**.
5. **Learning:** correction feed (status struck through, word-level diff, rationale, induced rule) and the playbook version timeline.
6. **Compare:** proof on the held-out RFP. Averaged scoreboard (mean, min–max over repeated runs), **Run 3× base vs vN**, cost per RFP in £ where prices are known, closed-model baseline, and row-by-row A/B with word diffs.

### The ripple (the wow beat)
**Teach & ripple** saves the correction, then in one call (`POST /api/ripple`, about 15–30s of real calls):
1. builds playbook vN+1, inducing a general rule from the correction through Mubit (`rfp.induce_rule`);
2. picks the held-out Thistle rows the rule could change, using BM25 relevance plus the correction's direction. An "up" correction (Partial → Comply) targets rows the model currently hedges; a "down" correction targets stronger claims. No LLM and no gold labels are used to choose rows;
3. re-drafts just those rows through Mubit and shows them as tracked changes: old status struck in red, new status written in, response diffed word by word, with a ✓/✗ against gold.

Held-out runs are always recorded as `metadata`, so the ripple never trains Mubit on Thistle.

---

## 8. Demo script (3 minutes, live)

### What the buttons do (so the presenter can explain them)
- **Teach** saves the correction in Redline only: the AI's answer, your corrected answer, your reason and the correction type. No model call, nothing sent to Mubit. It waits as "pending" until the next playbook build.
- **Teach & ripple** saves the correction, then in one action: builds the next playbook version (one `rfp.induce_rule` call per new correction, through Mubit), picks the held-out Thistle rows the new rule could change (plain code, no gold labels), re-drafts them through Mubit, and shows the before/after as tracked changes. Thistle calls are sent with `metadata`, so the ripple never trains Mubit.
- **How the model itself changes:** Mubit has no API for corrections, training or calling an adapter, so the app can't change the model directly. It doesn't need to. Every draft of a *practice* RFP with a playbook (v1+) is sent with full recording, so Mubit keeps those corrected calls as examples and trains the task adapter to copy them. The model update happens through normal use, and `scripts/warm_mubit.py` speeds it up. Correcting replies in the Mubit console is **not needed** (the base drafts you correct are sent with `metadata`, so Mubit never stored their content anyway).

### Before going on stage (about 30 minutes before)
1. Start the API **without** `--reload`, then the web app. Open http://localhost:3000.
2. Learning tab: **Load seed corrections**, then **Build playbook**. These are the guardrail rules (never agree to autonomous money decisions, never fix a price for unlimited scope). Without them a "don't hedge" rule can over-generalise: we saw it flip "auto-approve goodwill payments" to Comply.
3. Northstar drafted at base (rail step ②), so there are hedged rows to correct live. Pick one that hasn't been corrected yet (e.g. SEC-005, SEC-006, AI-002 or S-001 on a fresh database).
4. Compare: **Run 3× base vs vN** on Thistle, so the averaged scoreboard and the ripple's "before" exist (about 4 minutes, 156 calls, none recorded for training).
5. Mubit adapter: Tasks → Adapters shows a version **Passed**. If more examples are needed, run `python -m scripts.warm_mubit` (it only sends combinations not sent before). Start the adapter once in **Try models** beforehand: the first start can take a few minutes and there are 3 starts a day.
6. Get the Try models prompt ready: select Thistle in Redline, open **TR-05** in the Matrix (a run at the latest playbook), click **Copy Mubit prompt**, and paste it into Try models with **Side by side** on. Try models only adds the system prompt, so it needs this full message.
7. Record a backup video of the full flow.

### On stage
| Time | Beat | On screen |
|---|---|---|
| 0:00–0:20 | **Problem.** "Every RFP is the same task done thousands of times. AI drafts either over-promise, which becomes a binding commitment, or hedge, which loses points and can eliminate the bid on a mandatory row." | Overview |
| 0:20–0:40 | **Draft.** "Every row went through Mubit, grounded in our own knowledge base." Point at the trace panel: one call per row, request IDs, latency. | Matrix + trace panel |
| 0:40–1:15 | **Correct.** Open a hedged row ("Partial" for something we do as standard). Switch to **Comply** and give the reason: *"We do this as standard. Don't hedge because the evidence doesn't spell out every sub-detail; a needless Partial on a mandatory row can eliminate the bid."* The tracked-changes preview appears. | Row drawer |
| 1:15–1:55 | **Teach & ripple.** Narrate the overlay: "Redline turns my reason into a rule through Mubit, finds the rows it affects on a bank RFP it has never seen, and re-drafts them." Rows rewrite themselves: Partial struck through, Comply written in, ✓ against gold. | Ripple overlay |
| 1:55–2:25 | **Prove.** "Prove it on the whole RFP" → Compare. Averaged over 3 runs each on the held-out bank: about 87% → 95% accuracy, over-promises 1 → 0, traps 3/4 → 4/4 (quote the numbers from the day). | Compare scoreboard |
| 2:25–2:50 | **Model update.** Switch to Mubit **Try models**, with TR-05 already pasted: **Send to both**. "Every corrected call trained this small task adapter. Same judgement as the big model: Do Not Comply on auto-approving payments, from a model we own." | Mubit console |
| 2:50–3:00 | **Deliverable + money line.** **Open completed workbook**: Excel opens with the client's tabs filled in. "Without Mubit, the agent drafts. With Mubit, it learns how your company bids." | Excel |

**Backup plan:** the recorded video, plus stored runs. Every run is kept in `redline.db`, so Compare and Learning still work from earlier real runs if the network fails. Have a screenshot of the Try models side-by-side in case the adapter won't start.

**Likely judge questions:**
- *Isn't this just RAG plus a prompt?* → Retrieval supplies the facts and the playbook applies the judgement immediately. Mubit then distils the corrected calls into a task adapter, so the judgement moves into a small model you own. Every stage is a Mubit task.
- *Why not correct in the Mubit console?* → Bid managers work in the bid tool, not an AI console. Redline captures the correction where the work happens, and the corrected calls flow into Mubit as training examples automatically.
- *Did you overfit?* → Thistle is held out: a different industry and wording, gold labels written before any run, and no Thistle call is ever recorded for training (`x-middleware-record: metadata`). Ripple rows are chosen without gold labels. Numbers are averaged over repeated runs.
- *Does it ever get worse?* → Yes, and we show it. A narrow playbook scored 81% (below base), and a broad "don't hedge" rule once flipped "auto-approve payments" to Comply. Guardrail rules fix that, and the scoreboard counts over-promises and hedges separately.
- *Real data?* → Synthetic only. In a real firm, corrections happen naturally in every bid review.

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
| 7 | UI: demo rail, Overview, Document, Matrix + Teach & ripple, Learning, Compare (averaged), Open in Excel | ✅ built; needs a click-through in the browser |
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

**Latest, on the clean held-out Thistle Bank RFP (26 rows, `gpt-6-luna`, averaged):**

| Configuration | Runs | Status accuracy (min–max) | Over-promises | Hedged | Traps |
|---|---|---|---|---|---|
| Base, no playbook | 4 | 86.6% (85–88) | 1.0 | 2.5 | 3/4 |
| Playbook v2 (two retention corrections only) | 2 | 80.8% | 1.0 | 4.0 | 3/4 |
| **Playbook v5** (guardrail seeds + calibration corrections) | 3 | **94.9% (92–96)** | **0** | 1.3 | **4/4** |

The ranges don't overlap. A narrow playbook (v2) made things worse, while guardrails plus a general calibration rule fixed the over-promise trap (TR-05, auto-approving payments) and most hedges. Re-run on the day before quoting numbers.

**Earlier exploration (Meridian, before it became a practice pack):**

Held-out Meridian pack, 26 rows, one run per cell, scored against the gold labels:

| Model | Base v0 | Playbook v1 (4 corrections) |
|---|---|---|
| gpt-6-luna | 84.6% status accuracy, 0 over-promises, 4 hedged | **92.3%** |
| gpt-4o-mini | 92.3% | 88.5% |
| gpt-4.1-mini | 92.3% (1 over-promise) | not run |

- Grounded in a clean knowledge base, current models rarely **over-promise**: `gpt-6-luna` got all four trap rows right with no playbook. Its main failure is **under-claiming**: answering "Partially Comply" to requirements the company fully meets. On a mandatory row that can eliminate the bid (Northstar §8).
- Two hedging corrections on Northstar fixed hedging on *different* Meridian rows (REQ-01, REQ-16, SEC-07): real generalisation. The strict seed rules (AI-004, C-003) nudged some partials to "Do Not Comply", which the scoreboard catches.
- n is small and runs vary by a row or two, so rehearse with the numbers from the day.
- **Held-out hygiene:** a smoke test sent Meridian playbook runs to Mubit with full recording, so Meridian became a practice pack. **Thistle Bank** is the clean held-out RFP: no Thistle call is ever recorded for training, so adapter and playbook results on it are uncontaminated.
- **Mubit warm-up:** Mubit keeps only new examples, so re-running the same RFP with the same playbook adds nothing. `scripts/warm_mubit.py` skips combinations already sent; send new practice RFPs or a new playbook version instead.
- **Decision needed:** pitch "calibration" (agents both over-promise and hedge; corrections teach the team's judgement both ways) rather than the pure over-promise story in §1 and §8.
