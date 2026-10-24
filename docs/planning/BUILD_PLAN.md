# Redress: how it works, how the demo is wired, and who builds what

**In short:**
- Redress can do anything internal on its own: listening, triage, opening the case, starting the clock, routing, drafting.
- **Nothing reaches the customer without a handler clicking Approve.** Corrections happen at that approval step, so a wrong email is fixed before it's ever sent.
- The demo uses one laptop (backend, voice bot and console on the projector), Sultan's phone (the customer: a browser call plus the Gmail app), and one phone hotspot.
- One backend and one SQLite database hold everything.

Written Sat 24 Oct, around 21:05. Read this alongside the team README (`README.md` on `bank`). Where they differ, this file is newer for the topics it covers.

---

## 1. Why it's safe: what Redress can do alone, and what needs a human

| Zone | What happens | Who acts |
|---|---|---|
| 🟢 **Alone** (internal, reversible) | Transcribe · triage · flag vulnerability with the quote · open the case · start the regulatory clock · route to a team · draft the decision and letter · record every call in Mubit | Redress |
| 🟡 **Ava on the call** (customer-facing, tightly limited) | Listens, shows empathy, confirms the complaint is logged, explains how long it takes, offers a human. **She never decides, never promises money, never says "you'll get a refund."** | Ava, with the handler watching live and a **Take over** button |
| 🔴 **Needs a human click** | **Send any email or letter** · pay redress · close a case | Handler: **Approve & send** |

**How "agentic but safe" works:** the agent does the work, and a human signs off on anything that leaves the building.

**Ava's guardrail** (5 lines of plain code, no LLM): before each reply is spoken, check it for `£`, "refund", "guarantee", "compensat…" or "will definitely". If any match, swap in a safe line: *"I can't confirm an outcome on this call, but a specialist will review it and write to you."* The fixed system prompt says the same thing. It's the same idea as Vokal's hallucination guard.

**How this changes the bank's process:**

| | Today | With Redress |
|---|---|---|
| Who writes the response | A handler, 20+ minutes per case | Redress drafts 100% of cases |
| When the check happens | **After** sending: QA samples 5–10%, weeks later, and mistakes have already reached customers | **Before** sending: the handler checks every draft in about a minute |
| What happens to a fix | It stays in one person's head or a spreadsheet | It becomes a rule straight away, then a Mubit model update |

**Later (one sentence in the pitch, not built tonight):** autonomy is earned per letter type. A simple acknowledgement letter could auto-send after the handler has approved, say, 50 in a row without edits. Money decisions and vulnerable customers always stay with a human.

---

## 2. What the banker sees (and where every output goes)

Everything lives in **SQLite on the laptop**. The console (Next.js, on the projector) **polls** the backend: every 500 ms during a live call, every 2 s otherwise. That's simpler and safer than WebSockets on venue wifi.

| Screen | What's on it |
|---|---|
| **Queue** | Every call and email: channel icon, customer, category, ⚠ vulnerability, **clock countdown** ("PSR · 15 business days · 14 left"), and status (`live → drafted → needs review → sent`) |
| **Live call** | Captions for both sides · the triage card filling in · vulnerability flags with their quotes · clock started · **Take over** button |
| **Case** | Evidence on the left: the transcript or email, with highlights. On the right, Redress's draft: triage, decision, redress lines and the letter. Edit any field and give a reason → **Teach**. Then **Approve & send**. |
| **Learning** | Corrections and their reasons · playbook versions · rules created from corrections |
| **Compare** | Held-out complaints: base model vs latest playbook, averaged over 3 runs |
| **Mubit trace panel** | Every model call: task, `mreq_…` request ID, model, latency, recording mode |

Only two outputs ever reach the customer: **Ava's spoken words**, which are limited and guarded, and **approved emails**, sent from the bank's Gmail.

---

## 3. Email: real Gmail, set up in about 20 minutes

**Why Gmail:** the customer's email visibly arrives and the reply lands on a real phone. Real channels beat simulated ones with judges (we learned that at Tano).

**Setup (Abdulmaleeq does this; I can't create accounts):**
1. Create **two new Gmail accounts**: the bank (e.g. `thistlebank.complaints.demo@gmail.com`) and the customer, as the persona "Ellen Hart" (e.g. `ellen.hart.demo…@gmail.com`). Use new ones so no personal inbox goes on the projector. Google may ask for phone verification, so do this **now**.
2. On the **bank** account, turn on 2-Step Verification, then create an **app password**. Put it in `.env` as `GMAIL_USER` and `GMAIL_APP_PASSWORD`. **Never paste it in chat.**
3. **Backend, reading:** use `imaplib` against `imap.gmail.com:993`. Poll INBOX for unread mail every 5 s. A new message creates a case (`channel=email`) and runs the pipeline.
4. **Backend, sending:** use `smtplib` against `smtp.gmail.com:465`, only from **Approve & send**. Reply in the same thread (set `In-Reply-To` and `References` from the original `Message-ID`) so it threads properly in Ellen's Gmail.
5. Sign Sultan's phone into Ellen's Gmail. **Save the demo complaint as a draft** so on stage he just taps Send.

**Mock emails:** the 40 practice and 25 held-out cases are **JSON files loaded straight into the database**. They never go through Gmail. They exist to train Mubit and to score. Optionally, send about 8 older complaints into the bank Gmail tonight so the inbox looks lived-in if you show it.

**Fallbacks:**
- A dev-only **"Inject email"** button that puts the same email straight into the pipeline.
- If sending fails, show the approved letter in the app.
- Test both directions by **22:30**.

---

## 4. The call: who's who, and the devices

**Recommended setup:**
- **Sultan is the customer** on his phone.
- **Ava, the AI, answers.**
- **You are the bank handler**, supervising on the laptop: you watch it happen live, then correct and approve.

Don't build a human-to-human call. It doubles the audio work (two streams, separating the speakers), and the Mubit story is about the AI doing the repetitive work while the human teaches it.

```
Sultan's phone ──(browser call page, HTTPS via ngrok)──► Pipecat bot (laptop)
                                                          ├─ speech-to-text: Deepgram streaming
                                                          ├─ Ava's reply: Mubit (complaint.voice_turn), streamed, small model
                                                          └─ text-to-speech: Cartesia / ElevenLabs ──► audio back to the phone
                                         transcript lines ──► backend + SQLite ──► console (projector) polls /api/live
Sultan's phone (Gmail app) ──email──► bank Gmail ◄──IMAP poll── backend ──► case ──► handler approves ──SMTP──► Ellen's Gmail
```

**Devices:**
- **Laptop:** backend, voice bot, console.
- **Sultan's phone:** the call page and the Gmail app.
- **Your phone:** a hotspot that both the laptop and Sultan's phone join.

You don't need a second laptop or a cloud database.

**Phone audio connection, in order of preference:**
1. **Browser call using Pipecat's peer-to-peer WebRTC.** No third-party account. Put **the laptop and phone on the same hotspot** so it connects directly without extra relay servers. The phone mic needs HTTPS, so serve the call page through **ngrok**.
2. **Pipecat with Daily** (free account). Audio goes through Daily's servers, so it's more robust when the phone and laptop are on different networks.
3. **Expo stretch only, after 06:00:** a **Twilio number** that judges can ring from their own phones (Pipecat's WebSocket transport). It needs a paid Twilio account, because the trial plays a message and only calls verified numbers. Get a US number, because UK numbers need an address check.

**Call fallbacks:** a text-chat mode using the same `voice_turn` task, then a pre-recorded caller audio file run through the same pipeline, then the backup video.

**Voice latency:** gpt-4.1-mini through Mubit took about 1.4 s per call, without streaming, on Redline. Stream the replies, keep the voice system prompt short, and run triage in the background during the call. Measure from the end of speech to Ava's first audio by **23:30**.

---

## 5. The contract: copy this verbatim to the UI agents and the backend

Rule: change it in both places or not at all. The UI agents build against `USE_MOCK` with these exact shapes, so they're never blocked on the backend.

```text
GET  /api/cases                    → [{ id, channel: "call"|"email", customer: { name },
                                        category, vulnerable: bool,
                                        clock: { type: "SRC_3BD"|"PSR_15BD"|"DISP_8W", due_at },
                                        lane: "quick"|"senior",
                                        status: "live"|"drafted"|"needs_review"|"sent", created_at }]
GET  /api/cases/{id}               → { id, channel, customer: { name },
                                        evidence: { transcript: [{ speaker: "customer"|"ava", text, ts }],
                                                    email: { from, subject, body, received_at } | null },
                                        triage: { category, product, clock, severity, summary, confidence,
                                                  vulnerability: [{ driver: "health"|"life_event"|"resilience"|"capability",
                                                                    quote, citation }],            // citation e.g. "FCA FG21/1 · health"
                                                  consumer_duty: { products_services, price_value, understanding, support }
                                                                 // each { status: "ok"|"risk", quote|null }
                                                },
                                        decision: { outcome: "upheld"|"partially_upheld"|"not_upheld",
                                                    reasons: [string], redress: [{ label, amount_gbp }], confidence,
                                                    citations: [{ source, text }] },     // e.g. "Thistle fee policy §3.2", "DISP 1.6"
                                        lane: "quick"|"senior", lane_reason,
                                        letter: { subject, body,
                                                  checklist: { fos_rights, outcome_stated, reasons, redress, deadline } },
                                        playbook_version, traces: [{ task, request_id, model, latency_ms }] }
GET  /api/live                     → { active: bool, case_id, captions: [{ speaker, text, ts }], triage_partial,
                                        ava_checks: [{ ts, text, verdict: "pass"|"blocked", reason, replacement }] } (poll 500 ms)
POST /api/cases/{id}/correct       { field, value, reason }
                                   → { rule: { id, text }, playbook_version, ripple: [{ case_id, before, after }] }
POST /api/cases/{id}/approve       → { sent: true, to, message_id }
POST /api/cases/{id}/takeover      → { ok: true }
GET  /api/learning                 → { playbook_version, rules: [{ id, text, from_case, created_at }],
                                        corrections: [{ case_id, field, before, after, reason }] }
GET  /api/compare                  → { runs: [{ label, metrics: { vulnerability_recall, clock_accuracy, outcome_accuracy,
                                        redress_within_tolerance, letter_compliance, latency_p50_ms, cost_gbp },
                                        per_case: [{ case_id, correct: bool }] }] }
GET  /api/traces?limit=50          → [{ ts, task, request_id, model, latency_ms, record: "full"|"metadata" }]
GET  /api/dashboard                → { coverage_pct, cases_today, vulnerable_pct, clocks_at_risk,
                                        top_drivers: [{ category, count }], emerging: [{ category, change_x }],
                                        lanes: { quick, senior }, avg_review_seconds }
POST /api/rules                    { text } → { rule: { id, text }, playbook_version }   // plain-language rule (fast refresh)
GET  /api/preflight                → { last_run: { passed, total, ready: bool, signed_off_by, at,
                                        results: [{ persona, verdict: "pass"|"fail", issue, rule, transcript }] } }
POST /api/preflight/run            → same shape (runs the persona tests against Ava's voice_turn task)
POST /api/demo/inject-email        (fallback)        POST /api/demo/reset
```

**v1.1 (21:25):** added `confidence`, `citation(s)`, `consumer_duty`, `lane`, `ava_checks`, `/dashboard`, `/rules` and `/preflight`. These are the features taken from Aveni (§8). **The triage, decide and voice-turn JSON schemas must include the new fields before the prompts freeze**, or Mubit splits them into new tasks.

**Database tables (SQLite):** `customers`, `cases`, `transcript_lines`, `emails` (with `message_id` for threading), `corrections`, `rules`, `playbook_versions`, `traces`, `eval_runs`.

---

## 6. Who builds what

The team still needs to confirm names. The split assumes Sultan knows the Redline code.

| Track | Owner | First thing that has to work | Deadline |
|---|---|---|---|
| **A. Pipeline + Mubit**: triage, decide, letter, induce rule; corrections → playbook; warm-up script; eval | Sultan | One email case drafted end to end through Mubit | 22:30 |
| **B. Voice**: Pipecat bot, call page, guardrail, transcript events → `/api/live` | Abdulmaleeq (the risky integration, owned by you, per hard rule 1) | Phone browser → Ava answers through Mubit | **23:00** (cap: switch to text-chat fallback at 01:00) |
| **C. Email channels**: the Gmail accounts, IMAP poller, SMTP replies in thread | Abdulmaleeq (small job) | Send from Ellen's Gmail → case appears → approve → reply lands | 22:30 |
| **D. Console UI** | The UI agents | All screens on mock data with the contract above | 01:00, then switch to the real API |
| **E. Data**: Thistle Bank policies, 40 practice + 25 held-out cases, gold labels written **before** any run | Whoever isn't building; an agent can draft, a human checks | Files in `data/` | 22:30 |

**Key Mubit checkpoints:**
- At least 40 varied practice cases sent for **one** task (`complaint.triage` or `complaint.decide`) by **00:45**, so it trains before the 01:00 BST limit reset.
- Look at Tasks → Adapters every hour after that.

**Freeze 08:00 · submit 09:15 · code freeze 10:00.**

---

## 7. Tests to pass before the 08:00 freeze

- [ ] Ellen's Gmail → bank Gmail → case in the queue in under 15 s
- [ ] Approve & send → reply threads in Ellen's Gmail on the phone
- [ ] A phone call over the hotspot: Ava answers in under 1.5 s, captions and flags appear on the projector
- [ ] The guardrail catches "you'll get a refund"
- [ ] Teach → rule → ripple works on an unseen email
- [ ] Held-out scoreboard averaged over 3 runs. Held-out calls use `x-middleware-record: metadata`, **set in code**
- [ ] Mubit adapter **Passed** for one task, shown in Try models, and screen-recorded
- [ ] Every fallback tried once deliberately: inject email, text-chat call, recorded audio, backup video

---

## 8. Features taken from Aveni (ranked by what wins points)

Aveni has 250+ firms as customers, has raised at least £23m (£11m in 2024, £12m in 2026), and counts Lloyds and Nationwide as investors. Their feature set is proven, so we copy the **features and workflows**, not their name, logo, page text or screenshots. Sources: [Detect](https://aveni.ai/compliance/detect/), [Assure](https://aveni.ai/compliance/assure/), [Approve](https://aveni.ai/compliance/approve/), [File Check](https://aveni.ai/wealth/file-check/), [Intelligence](https://aveni.ai/intelligence/), [customer stories](https://aveni.ai/customer-stories/).

### P0: build tonight (cheap, and each one is a demo moment)

| # | Aveni feature | Redress version | Demo moment | Effort | Criterion it boosts |
|---|---|---|---|---|---|
| 1 | **Assure: live oversight of AI agents.** Every reply is scanned, and risky ones are "blocked, redacted or escalated mid-conversation", with a confidence score, regulatory citation and audit log | Each of Ava's replies is checked before it's spoken (plain code, plus the voice-turn schema). A blocked reply shows struck through on the live view with the reason, and the safe line is spoken instead. | Sultan baits Ava: *"So I'll definitely get my money back?"* Ava's draft reply "Yes, you'll get a full refund" gets **BLOCKED** live, and she says the safe line. | S–M | Demo, Usefulness |
| 2 | **Evidence citations on every finding**, plus regulatory citations and confidence (all their products) | Every flag and decision shows the quote, the rule ("DISP 1.6", "FG21/1 · health", "Thistle fee policy §3.2") and a confidence score | Click a flag and see the exact transcript line and the rule | S (schema) | Technical, Usefulness |
| 3 | **File Check: automatic triage.** Clean cases go straight through, and riskier ones go to reviewers with the evidence already gathered | **Review lanes**: *quick approve* (high confidence, no vulnerability, no money) vs *senior review* (vulnerability, redress above £0, or confidence below 0.8). Each case shows why it's in its lane. | The queue splits into two lanes, and Ellen's case lands in senior review because of hospital and money | S (plain code) | Usefulness (it answers "how is this safe?") |
| 4 | **File Check: "configure assessments in plain language"**, with a "framework update applies across all cases" | **Add a rule** box on Learning: *"From Monday, card disputes under £30 are refunded without investigation."* It goes into the playbook immediately. | The fast-refresh beat: type one sentence, and an unseen card-dispute email is handled the new way | S | Use of Mubit (fast refresh) |
| 5 | **File Check: a case can't pass without its required elements.** Every finding is cited | **Approve & send stays disabled** until the letter checklist passes: FOS rights, outcome stated, reasons, redress, deadline | Untick a checklist item and the button greys out | S | Usefulness, Technical |
| 6 | **Intelligence: three tiers.** Cheap classifiers (about 0.2 s), then their own FinLLM (Aveni says 25× cheaper), then GPT/Claude/Gemini as a fallback | **Pitch frame:** tier 1 = our rules (clocks, guardrail) · **tier 2 = Mubit adapters, one per recurring task, built from the bank's own corrected calls** · tier 3 = the big model through Mubit for drafting and edge cases | **The line:** *"Aveni spent 7 years and a 100-billion-token corpus building their specialist model. Mubit builds ours from the bank's own calls, overnight."* | 0 (slide) | **Use of Mubit** |

### P1: build if you're on track at 03:00

| # | Aveni feature | Redress version | Effort |
|---|---|---|---|
| 7 | **Consumer Duty scoring.** Every conversation is assessed against Consumer Duty, vulnerability and conduct | Each case is scored on the FCA's four Consumer Duty outcomes (products & services, price & value, consumer understanding, consumer support): ok or risk, with a quote. **Put it in the triage schema now, even if the UI shows it later.** | S schema / M UI |
| 8 | **Approve: test AI agents before launch** against simulated customer personas (including vulnerable ones), with results by persona and rule, sign-off and a "Ready for production" badge | **Ava pre-flight:** 12 synthetic caller personas (vulnerable, angry, scam victim, asks for a refund promise, wants a human…) run in text mode against `voice_turn` through Mubit. Rule checks score each one, giving a report like *"11/12 pass · Ready for production · signed off by Abdul."* That's also extra varied Mubit examples for that task. | M (2–3 h) |
| 9 | **Detect: board dashboards, trend analysis, outlier detection** | Tiles: **100% reviewed**, vulnerable %, clocks at risk, top complaint drivers, **emerging: "card disputes ↑3× this week"**, quick vs senior split, average review time | S–M |
| 10 | **Detect: one case across calls, emails, chat, SMS and documents** | Ellen's call, then her follow-up email from Gmail, shown on **one case timeline** (matched on customer) | S–M |

### P2: pitch only, don't build
- Coaching and handler outlier views (File Check / Detect)
- 500+ personas (Approve)
- CRM sync (Assist)
- Running inside the bank's own environment (only claim this if Mubit confirms adapters can be exported; RISKS M11)

### Their numbers to quote as market proof (say "Aveni reports…")
- **"83% faster compliance reviews: from 90 minutes to 15 minutes per case"** (Detect customer story)
- **"6x faster QA"** across 55,000+ customers (Key Group)
- **"15% to 100% coverage"** (Octopus Money)
- **"60% admin reduction"** (Prosser Knowles)
- £4.0M a year saved by firms that replaced manual sampling (Detect page)

Our own equivalent to **measure** in rehearsal: the handler's review time per case with Redress (target about 60 s) vs writing it from scratch.

### The honest difference (if a judge asks "so it's Aveni?")
Aveni says overrides "feed the next assessment release" of **their** model, built over seven years. In Redress:
- a handler's fix changes **the next call** straight away (the playbook);
- it changes **the bank's own** model overnight (a Mubit adapter);
- no model-building programme is needed.

Answer: *"Same proven workflow. The difference is that the learning belongs to the bank and happens tonight, not next release."*

---

## 9. Keys and secrets

- The app holds **only the Mubit key**, plus the speech, voice and email keys, all in `.env`.
- **Provider keys (OpenAI, Anthropic) go in the Mubit console under Provider keys, never in the app.** That's the hackathon rule, and it's what makes every call a Mubit training example.
- Never paste a key in chat. One was pasted on 24 Oct, so **rotate it** at platform.openai.com.
