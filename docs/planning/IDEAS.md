# Night Shift (Mubit) — ideas, pitches and research

**Verdict: build "Catch". It flags complaints and vulnerable customers in a lender's inbox, and every fix the QA team makes trains the firm's own model. Backup if the team wants the human story: Vokal v3, a speech model that keeps up with you. Pick by 20:00 tonight. Code freeze is 10:00 Sunday, about 15½ hours away counting the extra hour.**

Written Sat 24 Oct, 19:40. Everything below is either checked (source linked) or marked as something to check.

---

## 0. Before anything: what Mubit actually does (from docs.mubit.ai)

- **The proxy.** Change the base URL and use your Mubit key: OpenAI `https://api.mubit.ai/openai/v1`, Anthropic `https://api.mubit.ai/anthropic`, Gemini `https://api.mubit.ai/gemini`. Model IDs stay the same. Call it from the server only, because it doesn't answer browser CORS requests.
- **Tasks.** Calls that share the same **system prompt, tools, tool choice, output format and model** become one "task". Change one word in the system prompt and you get a new task. **Put anything that changes per call in the user message, never in the system prompt.**
- **Adapters.** At about **25 kept examples** a task trains an adapter, a small open model made for that one task. Mubit **tests each version against your provider model's answers** and marks it `Passed`, `Below target` or `Prompt only`. A passing version can be compared side by side in **Try models**, with latency shown.
- **Feedback.** The Requests page has **"Rate this reply: Good / Bad"** on every call, plus a Rating column. The public docs don't show an API for it.
- **The limits that shape the demo:**
  - Each workspace has a daily training limit and a pause between trainings. Both reset at **00:00 UTC, which is 01:00 BST tonight.**
  - Try models allows **3 adapter starts per UTC day**, and the first start takes a few minutes.
  - **There is no Mubit model ID.** The docs say your app can't call an adapter by name, so today the "after" shot lives in the Mubit console (Try models), not in your app.
  - **Mubit records prompts and replies by default**, so use synthetic data only.

### What this means for every idea

Adapters learn to copy the provider model's answers. So **a correction has to change what the provider model answers**, and then Mubit turns that into an adapter. The design that works whatever the office-hours answers turn out to be:

1. **Instant layer.** A human fixes an output. The fix goes into a corrections store. The 3 most similar past corrections are added **to the user message** of the next call (the task stays the same). The provider model gets it right straight away.
2. **Permanent layer.** Those corrected calls are kept examples in Mubit. The next adapter version learns the corrected behaviour, Mubit tests it, and it runs on a cheap open model.
3. **Amplify each correction.** On every fix, a separate "variations" call writes 10 realistic versions of the corrected case. Each one is run through the main task with the correction in context, so **one human fix becomes about 10 training examples**. This gets you to the "new version after N examples" mark tonight, not next week.
4. ~~Send `metadata.session_id` per case.~~ Don't. The team found it needs OpenAI's `store=true`. Use `x-middleware-record: metadata` for base and held-out runs instead, so they never train (see RISKS.md M16–M17).

### Ask the Mubit team at office hours, in the first 30 minutes (hard rule 1: the risky integration comes first)

1. Is there an API to attach a correction (a fixed answer, or Good/Bad) to a request ID? And does a Bad rating or a correction change what the adapter trains on?
2. Can our app call a trained adapter, by model ID or through automatic routing (the "Served by" column)? If not, is Try models the place to show it?
3. Is there any API for task and adapter status (kept-example count, version, test result), so our app can show it live?
4. How long does one training take? What are the daily training limit and the pause between trainings, and can they be raised for our project until the demo?
5. Can the 3 Try models adapter starts per day be raised for Sunday? Which open base models are used?

If the answers to 1–3 are "no API", the plan above still works: the corrections live in our app, and the "after" shot is the Mubit console in a second tab.

---

## 1. Top pick: **Catch** (working name)

**One line:** every customer message to a lender gets checked for a complaint and for signs of a vulnerable customer, and every fix the QA team makes trains the firm's own open model, which keeps up when the rules change.

**Why it wins here**
- **Use of Mubit.** It covers all three tracks in one demo: a recurring task (every message), owning the model (bank data shouldn't stay on a closed US model forever), and fast refresh (complaint rules keep moving).
- **Usefulness.** Under the FCA's DISP rules, a complaint is any expression of dissatisfaction, "whether justified or not". Missing one is a breach, and the venue is Canary Wharf.
- **Technical execution.** It's a classification task with a held-out labelled set, so the accuracy numbers are crisp and hold up under questions.
- **Demo.** One sentence on screen that everyone in the room can read.

**The task the app runs (one Mubit task):** a customer message goes in. Out comes JSON: `{complaint: yes/no, complaint_type, vulnerability: [health | life_event | resilience | capability], urgency, quote}`. The quote is the exact words that triggered each flag. The four vulnerability drivers come from FCA guidance FG21/1.

**Money facts (checked)**
- The Financial Ombudsman charges firms **£650 per case** it investigates in 2025/26, after the first 3 free cases a year, and proposed £680 for 2026/27. ([FOS budget 2025/26](https://financial-ombudsman.org.uk/files/324591/Financial-Ombudsman-Service-Plans-Budget-2025-26.pdf), [Mortgage Solutions](https://www.mortgagesolutions.co.uk/mortgage-news/2026/01/13/fos-lays-out-plan-to-up-fees-after-two-year-freeze/))
- In Oct 2024 the FCA fined Volkswagen Financial Services **£5.4m, plus £21.5m redress**. Part of the finding was failing to identify complaints. ([Ocorian summary](https://www.ocorian.com/fca-fines-volkswagen-financial-services-ps54m-failing-customers-financial-difficulty))
- The motor finance redress rules have moved all year: a consultation, deadline changes, then a June 2026 pause after a legal challenge. ([Paul Hastings](https://www.paulhastings.com/insights/client-alerts/update-fca-confirms-motor-finance-redress-scheme-key-points-for-motor-finance-lenders)) That makes it a real fast-refresh story.

### The demo (3 minutes on stage, plus a 30-second loop for the expo tables)

One screen in three columns:
- **Left:** the live inbox.
- **Middle:** Priya, the QA reviewer, with one-click fixes.
- **Right:** the model panel, showing which version is live, its held-out accuracy, missed complaints, and cost and latency per 1,000 messages for the closed model vs the adapter.
- **Keys:** `L` drops in the next scripted message, `G` jumps to the hero moment, `R` resets.
- **Fallbacks:** every live call falls back to a saved fixture if the wifi dies.

| Time | Beat | What the judges see |
|---|---|---|
| 0:00 | **A customer moment.** Sarah writes: "Third time asking. Your agent promised a callback that never came. I've just been signed off work and can't make Friday's payment." | The current model tags it "payment query". Pause on screen for 3 seconds. "Under FCA rules, that's a complaint, and Sarah is a vulnerable customer. The model missed both." |
| 0:25 | **The correction.** Priya ticks complaint, health and life event, then highlights "promised a callback that never came". | One click. The fix shows in Mubit's Requests, and 10 variations generate in the side panel. |
| 0:50 | **Instant.** Press `L`: a similar message arrives ("still waiting on the call you promised, and I'm in hospital"). | Caught straight away, with the quote highlighted. |
| 1:10 | **Permanent: the model update.** Switch to the Mubit console. | Task page: kept examples 25 → 60. Adapter history: v1 `Below target`, v2 `Passed`. Try models side by side on Sarah's message: the closed model on the left, our adapter on the right, both correct, adapter latency lower. |
| 1:50 | **Fast refresh.** "Monday: the motor finance rules change again. A new kind of message appears: 'did my dealer get commission on my car loan?'" | v2 misses it. Priya fixes 3, the amplifier makes 30 examples, and v3 catches it. Say it straight: "v3 trained at 6am from these exact corrections." |
| 2:30 | **Money screen.** A held-out set of 200 messages that were never used for corrections. | Missed complaints by version: closed model with prompt only, v1, v2, v3. "Each missed complaint that reaches the ombudsman costs £650 before any redress." Then cost per 1M messages for the closed model vs the adapter. **The last line, scripted: "Every fix Priya makes is now something the bank owns."** |

All numbers on the money screen get **measured tonight**. Don't invent any.

### Build plan (2–3 builders)

- **Data (first hour).** A generator script makes about 300 synthetic customer messages across 8 kinds: complaints, hidden complaints, vulnerability, motor finance and so on. Hand-label 200 for the held-out set, and keep them out of everything else.
- **Backend (Python FastAPI or Express).**
  - `/classify` calls the one Mubit task: fixed system prompt, retrieved corrections in the user message, `session_id` per message.
  - `/correct` stores the fix and triggers `/amplify`, which is a separate Mubit task that writes the variations.
  - `/eval` runs the held-out set and writes the scores to JSON.
- **Frontend.** One page with the three columns above. No login.
- **Mubit console** in a second browser tab for the adapter beats.

### The four checks
- **Saturation: it exists.** Aveni Detect (Edinburgh) sells complaints and vulnerability detection on its own FinLLM. ([Aveni](https://aveni.ai/blog/aveni-launches-enhanced-detect-to-provide-complete-case-level-outcome-testing-across-every-customer-interaction/)) Our angle: Aveni's pitch is a ready-made finance model (whether they also train per client hasn't been checked). Catch's pitch is that each firm's own QA fixes become its own model, refreshed when the rules move. A shipped competitor also proves the market.
- **Wrapper: medium risk.** An incumbent could add per-firm fine-tuning, but not in one sprint.
- **Money arc: pass.** The ombudsman fee, the fines, and cost per message.
- **Second use: pass.** Every message, every day.

### Assumption register (check today)
1. Mubit can train v2 from our corrections overnight. **Check:** office hours, questions 1 and 4.
2. Complaint teams really do miss complaints written in chat, and QA does sample and correct. **Check:** find a complaints, QA or compliance person in the room (it's Canary Wharf) and get one quotable sentence for the pitch.
3. A small adapter can match the closed model on this task. **Check:** Mubit's own test result on v1 by around 01:00.

---

## 2. Backup pick (your repo): **Vokal v3, a voice model that keeps up with you**

**One line:** for people whose speech is changing (MND, after a stroke, Parkinson's), every edit in Vokal's review box trains that person's own repair model, so it keeps pace as their voice changes. No 500-phrase sign-up session.

- **Why it's strong.** It's your own story and domain, since you're already running Whisper on TORGO. It has winning precedent:
  - **Gem-Care** won Digital Equity at Google's Gemma 4 Good Challenge by fine-tuning on dysarthric speech, taking word error rate from 32.7% to 19.0%. ([Google blog](https://blog.google/innovation-and-ai/technology/developers-tools/winning-entries-gemma-4-good-challenge/))
  - **Dream Assistant** won the Unsloth prize at Gemma 3n by fine-tuning on one speech-impaired user. ([Google blog](https://blog.google/innovation-and-ai/technology/developers-tools/developers-changing-lives-with-gemma-3n/))
  - LLM error correction on top of speech recognition for dysarthric speech is published research (La Quatra et al., Interspeech 2025, [arXiv 2505.20163](https://arxiv.org/abs/2505.20163)). It works best on sentences, not single words.
- **The Mubit loop.** Whisper's raw text, plus its alternative guesses and the person's recent phrases, go into one Mubit task, which returns the sentence they meant. The edit in the review box is the correction, and it trains a per-person adapter. **Fast refresh is the whole point:** MND is progressive, so month 6 speech isn't month 1 speech.
- **The demo.** Play real TORGO dysarthric clips: speech recognition gets it wrong, the repair layer gets most of it, the person fixes one word, the model updates, and the same speaker's held-out clips go from X% to Y% of sentences right.
- **The weak spot is the money arc.** The last screen would have to be time (edits per sentence, words per minute), not £. It also needs speech recognition done ahead of time for the demo, so it doesn't depend on a live mic in a loud room.
- **Saturation.** Google Project Relate personalises recognition but needs 500 recorded phrases ([The Batch](https://www.deeplearning.ai/the-batch/project-relate)). Voiceitt also exists. Our angle: it learns from everyday edits and keeps up as speech changes.

## 3. Third option: **First Line AI → triage that learns from the duty GP**

Patient messages after starting GLP-1s or other medicines get triaged as urgent, routine or "no action", with a reason. The duty GP's re-triage is the correction. Own your model: NHS data. **Why it's third:** Accurx, PATCHS and Klinik already do triage, and you'd need one of your four clinicians to give a quote tonight. **The upside:** you have that clinician network.

---

## 4. Your GitHub, scored for a Mubit pivot

**Rule check: "all project code is written during the event."** You can reuse an idea, your knowledge and open-source libraries. **You can't reuse old repo code.** Start a fresh public repo.

| Repo | Recurring LLM task inside it | What the correction would be | Fit | Verdict |
|---|---|---|---|---|
| **Vokal** | Repair speech-recognition text into the intended sentence | The edit in the review box | High (fast refresh) | **Backup pick** |
| **First-Line-AI** | Triage patient side-effect messages | The GP re-triages | High | Third option |
| **swypr** | Draft DM replies in the creator's voice | The creator edits the draft | High, but "support replies" is what everyone will build | Safe but crowded |
| **FignalAI** | Find and patch Verilog bugs | The simulator, not a human, marks the fix right | Clever, judges hard to read | A niche wow |
| **Wama-AI** | Pull the ask, accepts and claims out of a DM | The fixed extraction | Medium | Too small on its own |
| **Offload** | Grade and price clothes from photos and voice | The reseller's re-grade | Medium; needs images, and Mubit image support is unconfirmed | Ask at office hours |
| **mise** | Read supplier messages into order lines | The owner's fixes | Medium | Weak correction moment |
| **Kairo-AI** | Re-check patients against new guidelines | The clinician overrides | Medium (fast refresh) | Needs clinical weight |
| **xrpl-decode-detect** | (a model, not an LLM) | — | Low; points toward AML alert triage | See idea bank |
| **nearly** | Video events into a closed question | — | Low (vision model) | — |
| suede, Bould, FLIQ_AI, iterate-hack, FEMUR, Holdback-AI, Sign-Language | — | — | Low | — |

## 5. Other ideas I'd build here (the idea bank)

| Idea | Task Mubit learns | Correction | Track | Why it might lose |
|---|---|---|---|---|
| **AML alert triage** (grows out of your XRPL work) | Alert → false positive or escalate, with a reason | The analyst's decision | Own + refresh | Alerts are hard to read on stage |
| **Customs code classifier** (UK Trade Tariff API is free) | Product description → 10-digit commodity code | The broker's fix | Refresh (tariffs change) | No customs expert in the room |
| **Invoice → ledger code for bookkeepers** | Line item → nominal code and VAT treatment | The bookkeeper recodes | Recurring; one adapter per client | Dext and AutoEntry already do it |
| **Regulatory change triage** (DTCC 2025 Gold was CIBC's version) | New rule text → "applies to us?" plus which controls | Compliance's call | Refresh | Long documents, slow demo |
| **Debt collection message checker** (Claimsio won at ElevenLabs Warsaw and MAS) | Draft → compliant or not, then a rewrite | The compliance officer's edit | Recurring | Overlaps with Catch |
| **Evals as a model** | Output → pass or fail against your rubric | The human grade | Own | Too meta for "usefulness" |

---

## 6. Research: about 125 winning projects across about 25 events

**Coverage, honestly.** Readable winner lists came from: Anthropic's three Built-with-Claude hackathons, Google's Gemma 3n and Gemma 4 Good, ElevenLabs Worldwide (all cities), TreeHacks 2025 and 2026, HackMIT 2025, HackLondon 2024, IC Hack 2025, Lovable × Project Europe, START Hack 2026, AI Tinkerers Paris, OpenAI Agents Everywhere, Guidewire DEVHack, the Vista Agentic AI hackathon, Zurich's Agentic AI challenge, the Circle × lablab Arc hackathon, DTCC Innovate AI 2025 and 2026, the MAS Hackcelerator 2025, the FCA greenwashing TechSprint, the FHFA TechSprint, Microsoft Agent Academy 2026, the Salesforce TDX Agentforce hackathon, the Databricks Free Edition hackathon, Impetus × AWS, and ETHGlobal Bangkok. **No usable winner lists turned up** for Cal Hacks, PennApps, Hack the North, HackZurich, Junction, the bank-run hackathons (JPMorgan, Goldman, Barclays), Mistral or WeaveHacks, so none are guessed here.

### What won (patterns)
1. **At the finance and enterprise hackathons, narrow back-office jobs with a human approval step won:** regulatory change (DTCC Gold 2025), post-trade exceptions (DTCC Silver 2026), claims intake (Vista and Zurich), contract-clause scoring (Microsoft). Each was pitched on a saved-time or saved-money number.
2. **At model-lab hackathons, accessibility plus a measured fine-tune won:** Gem-Care (word error rate 32.7% → 19.0%), Dream Assistant, MindBridge, PathOS.
3. **Almost no winner showed a measurable improvement from user feedback.** That gap is exactly what Mubit fills, so make the improvement curve the hero of the demo.
4. Live voice and agent demos with a "did that just happen?" moment won ElevenLabs-style events (GibberLink).

### Best fits for "add Mubit to a past winner"

| Past winner | Mubit twist | Money moment |
|---|---|---|
| CrossBeam (Opus 4.6, 1st): housing permit review | Reviewer fixes become one model per city's rules | Minutes per permit; a new city onboarded in an hour |
| Medkit (Opus 4.7, 1st): grades clinical answers | Instructor re-grades become the grader | Agreement with the instructor goes up as cost goes down |
| ARIA (Opus 4.7, Managed Agents): factory fault → work order | Technician fixes, one model per factory | The right work order on the alarm that was wrong a minute ago |
| Gem-Care (Gemma 4 Good): dysarthric speech | Every corrected sentence becomes a per-person update | Word error rate falling live |
| Felix (Vista, 1st): insurance claims intake | Adjuster fixes severity and fraud labels | Cost per claim, time to assignment |
| Tiba (Arc, 1st): medical PDFs → billing codes | Biller fixes the code, one model per clinic | Claim denials avoided |
| CIBC regulatory change (DTCC Gold 2025) | Compliance fixes "applies to us?" | Months of manual review saved |
| NovaMind (DTCC Silver 2026): post-trade exceptions | Ops analyst resolutions | Share of exceptions resolved automatically |
| VendorGuard (Microsoft, 1st): contract clauses rated red, amber or green | Reviewer flips amber to red | The same contract re-run, the verdict flips |
| Claimsio (ElevenLabs Warsaw 2nd, MAS winner): compliant debt collection | Compliance edits to drafts | Fewer human touches per message |
| Hawkwatch (TreeHacks 2025 grand prize): CCTV alerts | The operator's dismiss or report clicks | False alerts per hour falling |
| Unstuck (ElevenLabs NYC, 1st): a docs agent for any site | Support-lead fixes, one adapter per customer | Deflection up, cost per ticket down |

### Full winners list

**Model labs and AI infrastructure**
- **Anthropic, Built with Opus 4.8 (2026):** Tekton (1st, 3D Tang Dynasty architecture traced to sources), Sim Francisco (2nd, census digital twin that polls a synthetic city), Custom Universe (3rd, one photo → editable 3D scene).
- **Anthropic, Built with Opus 4.7:** Medkit (1st, simulated patients graded against guidelines), Wrench Board (2nd, electronics repair diagnosis), Maieutic (3rd, spec-first coding environment), Virtual Puppet Theater, MaestrIA (home repair diagnosis and cost estimates), ARIA (factory diagnostics → work orders).
- **Anthropic, Built with Opus 4.6:** CrossBeam (1st, permit compliance review), Elisa (2nd, block coding for kids), PostVisit.ai (3rd, plain-language visit notes), TARA (dashcam → road investment appraisal), Conductr (live music backing).
- **Gemma 3n Impact Challenge (2025):** Gemma Vision (1st, assistant for blind users), Vite Vere Offline (2nd), 3VA (3rd, pictograms → sentences), Sixth Sense for Security Guards (4th, threat triage), Dream Assistant (Unsloth prize), LENTERA (Ollama prize), My Jetson Gemma (NVIDIA prize).
- **Gemma 4 Good Challenge (2026):** GEM-4 (1st, assistive robot), Trido (2nd), PenguinAgent (3rd), DEMENTOR (4th), Acuífero·Vigía (flood warning), TrueVoice (voice-scam detection), Gem-Care (dysarthric speech), CodeBuddy (Socratic tutor), Project Rosie (oncology), Gilbeot (navigation for seniors), PreVillage (WhatsApp guide to Nepali government services), PathOS (histopathology screening), MindBridge (Hindi mental-health screening), KawanIsyarat (sign language).
- **OpenAI gpt-oss-20b Red Teaming:** Mind the Gap (Holistic AI / UCL, top 10).
- **ElevenLabs Worldwide (2025):**
  - London: GibberLink (London 1st and global top prize), Espresso Labs, Vox Populi.
  - New York: Unstuck (1st), Procuro (2nd, calls suppliers about delayed parts), Show me how.
  - San Francisco: Dealwise (1st, phones businesses for quotes), Roadmate, Hippo.
  - Warsaw: DeepSky (1st), Claimsio (2nd), Voyagr (3rd).
  - Online: Hugo Tour Guide (1st), Pep, Agent SFX.
  - Bangalore: lossfunk (1st), ECHO AI, Pochinki.
  - Seoul: Voice Guardian (1st), AMUSH, PrintMoneyAI.
  - Partner prizes: Playcade (fal.ai), PostHog Meeting Copilot (PostHog), Voyagr (Lovable).

**University and startup-ecosystem hackathons**
- **TreeHacks 2025:** Hawkwatch (grand prize, CCTV alert triage), BlinkAI, OmNom, WingNote (Gemini prize, nurse documentation), SurviveX.
- **TreeHacks 2026:** Shepherd (grand prize, smart cane), HackOverflow.
- **HackMIT 2025:** AI insurance-claim generator (track win).
- **HackLondon 2024:** BRICK@ed.up (sorts mail by priority).
- **IC Hack 2025:** Cascade (Helsing prize, supply-chain risk).
- **Lovable × Project Europe:** GoodOmen (1st). Search snippet only, not checked on a fetched page.
- **START Hack 2026:** Runtime Terrors (HVAC signals → plain-language insights).
- **OpenAI Agents Everywhere:** Sidekick, Arto, ScreenMate. Search snippets only, not checked on a fetched page.
- **AI Tinkerers Paris:** Active Pulse, Dragonfruit, Discovery, SoccerVision, FidelityAI, Dream Path. Search snippets only, not checked on a fetched page.

**Finance, insurance and enterprise**
- **Guidewire DEVHack 2025:** GigGuards (1st), ESGverse (2nd), HEXperience (3rd).
- **Vista Agentic AI 2025:** Felix by Duck Creek (1st, claims intake).
- **Zurich Agentic AI 2025:** AgentricAI (travel claims), Etio (IFRS 17 reporting), ZuriFault (motor liability), Interloom, WordLift.
- **Circle × lablab Arc (2025):** Tiba (1st, medical billing codes), Arc Pay, SOLRARC, ArcAgent.
- **DTCC Innovate AI 2025:** CIBC Regulatory Change (Gold), Cyber ThirdEye (Silver), Xypher by Deutsche Bank (Bronze, trade validation), Cipher Sentinel (academic, AML), Accenture Regulatory Compliance.
- **DTCC Innovate AI 2026:** Snowflake × DTCC threat hunting (Gold), NovaMind by Deutsche Bank (Silver, post-trade exceptions), OpsFlow (Bronze), ACT!vated Intelligence (internal audit).
- **MAS Hackcelerator 2025:** ActuaViz (insurance PDFs → data), Claimsio, Oxford Risk, IDVerse.
- **FCA/GFIN Greenwashing TechSprint (2023):** Impact Scope, GaiaLens, Neotas, a King's College London team, FiData.
- **FHFA TechSprint 2024:** Team Arsenal (accessibility compliance checks).
- **Microsoft Agent Academy 2026:** VendorGuard (contract clauses rated red, amber or green), Performance Development Assistant, Meeting Tasks Agent, Engagement Hub, SprintForge, Autonomous ITSM Platform, Client Kick-off Skill, FrostByte.
- **Impetus × AWS:** Privacy Guardian Agents, GovGuard.
- **Salesforce TDX 2025:** Agent Halo (grand prize, claims coordination).
- **Databricks Free Edition 2025:** space-weather grid risk (2nd).
- **ETHGlobal Bangkok 2024:** DAOGenie (finalist).

---

## 7. Timeline (BST; clocks go back 02:00 → 01:00 tonight)

| Time | What | Rule |
|---|---|---|
| 19:45–20:00 | Pick the idea, add your twist, name the owners | — |
| 20:00–20:30 | Mubit office hours (the 5 questions). Get one call going through Mubit and showing in Requests | Hard rule 1 |
| by 21:30 | **Integration cap.** Seed generator done, 60+ calls of the task sent, the task visible in the Tasks page | If it's not working, switch to the fallback |
| by 00:45 | v1 adapter training started, **before the 01:00 BST training-limit reset** | — |
| 01:00–06:00 | Correction loop, amplifier, held-out eval; v2 trains after the reset | Take turns sleeping |
| 06:00 | Fast-refresh beat: motor finance corrections, then v3 | — |
| **08:00** | **Feature freeze.** Screenshots now | Hard rule 2 |
| 08:00–09:15 | 3 run-throughs: one recorded and watched, one where you kill the wifi on purpose. Use at most 1 Try models start, and save 2 for judging | Hard rule 3 |
| **09:15** | **Submit** | Submit 45 minutes early |
| 10:00 | Code freeze. 10:30 expo judging (30-second loop). 12:30 finalists on stage | — |

Set phone alarms now for 00:45, 08:00, 09:15 and 10:00.

## 8. Rules check (compliance pass)
- All code is written during the event, in a fresh public repo registered with Max (`/team create`).
- **Every** LLM call goes through Mubit, including the amplifier and any judge or eval calls.
- Synthetic data only, because Mubit records content by default. That also keeps real customer data out of the demo.
- At least one teammate is on site for Sunday's demos.
- No made-up numbers on the money screen. Everything comes from tonight's eval run.
