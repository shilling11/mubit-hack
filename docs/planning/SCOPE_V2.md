# Scope v2: the review after the call (proposed 21:40, not locked yet)

**In short:** cut the live voice agent and the live checks on it. Redress does **one recurring job: the review every complaint call gets after it ends.** That review:
- decides whether it's a complaint under the FCA rules, which deadline applies, and whether the customer is vulnerable;
- checks the agent's conduct against a QA scorecard;
- picks the next action: escalate to the right manager, and draft the customer email.

It runs on **100% of calls instead of the 1–2% QA samples today.** QA reviewers correct it, and the corrections train the bank's own model through Mubit.

---

## Why this is the right cut

- **The QA gap is real and sourced.** "Traditional QA samples just 1–2% of interactions, leaving most vulnerable customer experiences completely unmonitored." That's ContactBabel, from a survey of 200+ UK contact centres ([ContactBabel](https://www.contactbabel.com/?p=12967)). Vendors put it at 2–5% ([Aircall](https://aircall.io/blog/ai-quality-assurance-call-center/)). Aveni says 5–10%.
- **The FCA angle comes built in.** Each review answers: is it a complaint under the FCA's DISP rules, which deadline (3 business days, 15 business days or 8 weeks), and which vulnerability driver (FG21/1).
- **It's the most "Mubit" task there is:**
  - The same structured job runs after every call: the "recurring tasks" track.
  - It's high volume, so cost matters: the "own your intelligence layer" track.
  - The rules change, like the car-finance commission rules this year: the "fast refresh" track.
  - **One** hero task trains faster than the five in the old plan (RISKS M19).
- **It removes the riskiest build.** There's no AI voice agent, no speech synthesis and no live voice pipeline. The call is just a **recording**. Banks record calls already.

## Who already does this (startups)

| Company | What it does after the call | Proof it's real |
|---|---|---|
| **Aveni Detect** (Edinburgh) | Reviews 100% of conversations against the firm's framework, with evidence, overrides and audit | £23m+ raised; Lloyds and Nationwide invested ([Aveni](https://aveni.ai/compliance/detect/)) |
| **EvaluAgent** (Middlesbrough) | Auto-QA scoring; tags complaint escalation and vulnerability indicators | $20M Series A, 2023 ([TechCrunch](https://techcrunch.com/2023/06/23/evaluagent-raises-20m-to-build-out-software-to-evaluate-call-center-agents/)) |
| **Recordsure** (London) | ReviewAI: says it "reduce[s] reliance on random sampling" and flags high-risk cases for human review | A Tier 1 UK bank; NatWest trial ([Intelliflo](https://www.intelliflo.com/partners/integrated-partners/recordsure-review-ai/), [Retail Banker International](https://www.retailbankerinternational.com/news/natwest-trials-artificial-intelligence-compliance-technology/)) |
| **Voyc** (Amsterdam) | Flags complaints and vulnerable customers on 100% of calls | $2M seed, 2025 |
| **Observe.AI** (US) | Auto QA fills in QA forms for every interaction | Product since 2022 ([CX Today](https://www.cxtoday.com/contact-center/observe-ai-launches-a-quality-assurance-automation-solution/)) |
| **Convin** (India) | "Automate 100% of call quality assurance" | $6.5M |
| **Dialpad, Verint** | Post-call wrap-up bots: summary, outcome code, follow-up tasks | Big incumbents ([Verint](https://www.verint.com/blog/long-story-short-introducing-the-verint-interaction-wrap-up-bot/)) |

## Hackathon wins with the same shape: something happens, AI triages and routes it, a human signs off

| Winner | What it did |
|---|---|
| **Hawkwatch**: TreeHacks 2025 **grand prize** | Triages CCTV alerts; the operator dismisses or reports |
| **Felix** (Duck Creek): Vista Agentic AI 2025 **1st** | Triages insurance claims after the event |
| **NovaMind** (Deutsche Bank): DTCC 2026 **Silver** | Handles post-trade exceptions with an audit trail |
| **Autonomous ITSM**: Microsoft Agent Academy 2026 **1st** | Triages tickets, with one-tap manager approval |
| **Meeting Tasks Agent**: Microsoft Agent Academy 2026 **2nd** | Turns meeting transcripts into tasks |
| **AI Alliance**: lablab ChatGPT + Whisper hackathon **finalist** | Automated QA auditing of support calls ([lablab](https://lablab.ai/ai-articles/chatgpt-api-and-whisper-api-global-hackathon-winner-announcement)) |

**No winner has done regulated complaint QA on 100% of calls with a model that learns from reviewers.** That's our spot.

---

## The one recurring task: `call.review` (one Mubit task, schema frozen early)

**Input** (user message): the call transcript, split by speaker, plus the playbook rules.

**Output** (strict JSON):
```text
{ summary,
  complaint: { is_complaint, category, quote, citation },          // DISP definition
  clock: "SRC_3BD" | "PSR_15BD" | "DISP_8W",
  vulnerability: [{ driver: health|life_event|resilience|capability, quote, citation }],   // FG21/1
  qa: [{ item, status: "pass"|"fail"|"n/a", quote }],              // the agent's conduct, see below
  next_actions: [{ type: "escalate"|"acknowledge"|"callback", to, reason }],
  confidence }
```

**QA scorecard items, taken from FCA expectations:**
1. Recognised it as a complaint
2. Explained the next steps and the deadline
3. Spotted the vulnerability and offered support
4. Made no promise of an outcome
5. Checked the customer understood
6. Mentioned the Ombudsman's role if relevant

**Plus two light tasks:**
- `email.draft`: the escalation email and the customer acknowledgement.
- `rule.induce`: turns a correction into a rule.

All three go through Mubit. Only `call.review` is the hero we warm up to 25+ kept examples.

## How it's safe (same rule as before)

- **Internal actions happen automatically:** the review, opening the case, starting the clock, **the escalation email to the manager**.
- **Anything to the customer waits for a human:** the acknowledgement email needs **Approve & send**.

## The demo (flashy beats only)

| Time | Beat | Why it lands |
|---|---|---|
| 0:00 | **"QA hears 1 in 50 calls."** A wall of 100 tiles, one per call today. "Today's QA" lights **2** of them. **Then Redress reviews all 100**: every tile flips, and complaints and vulnerable customers light up. *"The 2-call sample found none of the 9 missed complaints. Redress found all 9."* Numbers come from the synthetic batch, so measure them. | The 1–2% problem, shown in 10 seconds |
| 0:30 | **A real call.** Sultan rings your phone on speaker next to the laptop. You're the bank agent; he's Ellen: fees while in hospital, and annoyed. You handle it a bit badly on purpose. | Real, human, no AI voice |
| 1:00 | **Hang up, and the review lands in seconds.** Complaint ✓ · 15 business days · Vulnerable: health ("I was in hospital") · QA: ✗ "didn't explain next steps". **The manager's Gmail gets an escalation email automatically** (show it on a phone). The customer acknowledgement waits for approval. | After-call work done in seconds, and it's FCA-aware |
| 1:40 | **The correction.** The QA reviewer fixes something Redress missed and gives one line of reason. The rule is created, then re-run on the 100: **more tiles light up**. | Correction → better straight away, the "recurring tasks" track |
| 2:15 | **The model update.** Mubit console: `call.review` version 2 passed, and Try models side by side with the big model. | **Use of Mubit** |
| 2:40 | **Money.** Calls reviewed: 2% → 100%. Reviewer time per call. Cost to review 1M calls on the big model vs our own model (measured). Approve & send: the acknowledgement lands in Ellen's Gmail. | The money screen |

## What changes in the build (if you lock this)

- **Voice track becomes a call-recording track:**
  - a "Record call" button in the console (browser mic) → on hang-up, upload the audio → speech-to-text with speakers separated (Deepgram's pre-recorded mode with `diarize=true`) → transcript → `call.review`.
  - That's about **2 hours instead of 6+**, with no Pipecat, text-to-speech or ngrok. Fallback: a pre-recorded audio file.
- **Data:** generate **100 synthetic call transcripts** (through Mubit) across categories, with 9–12 hidden complaints and vulnerable customers. These feed the wall, the eval (keep 25 held out with `metadata`), **and** Mubit's warm-up: 75 varied calls, well past 25 kept examples.
- **Gmail:**
  - three accounts: bank complaints inbox, **complaints manager** (gets escalations automatically), customer Ellen (gets the acknowledgement after approval);
  - only the sending side is needed for the demo, plus an optional poller for emailed complaints.
- **Cut:** Ava the AI voice agent, the live checks on her (Aveni's Assure), the pre-launch tests (Aveni's Approve), the voice-turn task, the live captions.
- **Keep from the Aveni list:**
  - evidence and rule references on every flag;
  - quick vs senior review lanes;
  - plain-language rules (fast refresh);
  - the letter checklist that gates Approve;
  - the dashboard (it becomes the **100-tile wall**);
  - the three-tier pitch line.

### Contract changes (v2, apply to both the UI and the backend)
```text
POST /api/calls                    multipart audio → { case_id }            (record → transcribe → review)
GET  /api/wall                     → { total, sampled_ids: [id], stats: { complaints, vulnerable, missed_by_agent,
                                        found_by_sample, found_by_redress }, tiles: [{ id, complaint, vulnerable,
                                        qa_fail_count, sampled: bool }] }
GET  /api/cases/{id}               + qa: [{ item, status, quote }],
                                   + next_actions: [{ type, to, reason, draft: { subject, body }, status: "sent"|"awaiting_approval" }]
REMOVED: /api/live ava_checks, /api/cases/{id}/takeover, /api/preflight*
```
