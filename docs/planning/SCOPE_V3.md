# Scope v3: Redress for QA firms (proposed 22:00, not locked yet)

**In short:**
- **Banks *are* allowed to run their own QA.** They can also outsource it, and many do. Either way, the people checking must be independent of the people doing the work. That rule is probably where the "third party" idea comes from.
- **Selling to an outsourced QA firm is a strong angle.** One firm serves many banks, so you get one Mubit adapter per bank, a better cost per reviewed call, and the firm owns the model built from its analysts' labels.
- **Every feature below is copied from a live, funded product.** Nothing is invented.

---

## 1. Is outsourced QA a legal requirement? No, but independence is

| What we checked | What it says | Source |
|---|---|---|
| Can a bank outsource? | Yes, but "your firm is responsible and accountable… firms cannot delegate any part of this responsibility to a third party" | [FCA, outsourcing](https://www.fca.org.uk/firms/outsourcing-and-operational-resilience), [SYSC 8](https://handbook.fca.org.uk/handbook/sysc8/sysc8s1) |
| Must the checkers be independent? | **Yes.** The compliance function must operate independently, and "the relevant persons involved in the compliance functions must not be involved in the performance of the services" they monitor. **This is probably the rule you were remembering.** | [FCA Handbook SYSC 6.1](https://www.handbook.fca.org.uk/handbook/SYSC/6/1.html) |
| Do banks run QA in-house? | Yes. **United Trust Bank** has an in-house QA Manager using Voyc. A **major UK retail bank** runs QA on 5,000 mortgage calls a month itself, using Recordsure. | [Voyc customers](https://voyc.ai/customers), [Recordsure case study](https://recordsure.com/case-studies/improving-oversight-and-quality-assurance-across-mortgage-advice-conversations/) |
| Do banks outsource it? | Yes, a lot. **TCC Group**: outsourced compliance, QA & oversight, complaints and remediation, with 4,000+ regulatory engagements. **Huntswood**: 280,000+ complaints a year, 139,000+ of them in banking. **KPMG** runs managed complaints with QA built in. **Target Group** does 100% quality checking on high-risk processes. | [TCC Group](https://recordsure.com/tcc-group/), [Huntswood](https://www.huntswood.com/?p=79717), [KPMG](https://kpmg.com/uk/en/services/consulting/managed-services/complaint-handling.html), [Target](https://targetgroup.com/about/case-studies/case-study-complaints-servicing-for-a-leading-uk-mortgage-provider) |

**So the customer can be either.** Pitch the **outsourced QA firm**, because it makes the Mubit story strongest: many clients, thin margins, and expert labels as its main asset. Say on stage: *"Banks can do this in-house too. Same product."*

## 2. Proof that QA teams already use AI to audit calls (real, named examples)

| Who | What they do with AI | Results (as reported) |
|---|---|---|
| **A UK consultancy doing managed file reviews** for its clients (Recordsure client since 2016) | AI classifies and dates documents and surfaces the relevant passages. **Skilled reviewers still make the final call** and record the evidence behind it. | **Review time down 50%**; efficiency up 50% against a 20–25% target; 92% accuracy on document classification. [Case study](https://recordsure.com/case-studies/document-intelligence-consultancy-managed-services-uk/) |
| **A major UK retail bank** (Recordsure since 2018) | Automated risk scoring and quality checks on every mortgage call, sorted into themes that match the bank's own QA checklists. High-risk calls go to humans first. | **QA coverage up from under 5% to 100%** · review time down more than 50% · **95% human–AI agreement, checked by users** · 60,000+ calls a year · 400+ users. [Case study](https://recordsure.com/case-studies/improving-oversight-and-quality-assurance-across-mortgage-advice-conversations/) |
| **Zego**, Head of Technical Claims, QA and Complaints | *"Voyc reviews every conversation our AI and human agents have with customers and flags anyone who's unhappy or in a vulnerable situation. It's helped us improve how we identify complaints."* | [Voyc customers](https://voyc.ai/customers) |
| A 30-person motor insurance renewals team (Voyc) | Spotting vulnerable customers | **Vulnerability identification up from 88% to 96%** |
| EvaluAgent customers | Automated QA scoring | **Audit time from 24 min to 6 min 17 s** · QA productivity up 285% · pass rate from 73% to 85% · checks up from 900 to 6,000. [EvaluAgent](https://www.evaluagent.com/auto-quality-assurance/) |
| **Huntswood**, an outsourced complaints firm | Complaints360 uses AI for complaint triage, response drafting and spotting risk. "Complaints specialists retain oversight of critical decisions." | [Huntswood](https://www.huntswood.com/?p=79717) |
| Industry-wide | Traditional QA samples **1–2%** of interactions; **only 10%** of UK contact centres use AI to support vulnerable customers (a survey of 200+ centres) | [ContactBabel](https://www.contactbabel.com/?p=12967) |

## 3. What the startups actually do, from their own sites

### EvaluAgent (Middlesbrough; $20M Series A) — [AutoQM page](https://www.evaluagent.com/auto-quality-assurance/)
- **Auto QA scorecard:** weighted criteria and an overall pass/fail. Their example: Greeting 10/10 · Verification 15/15 · **Empathy 3/15** · Resolution 7/15 → **65% FAIL**, plus a count of **auto-fails**.
- **Custom scorecards:** weight each criterion, set **auto-fail logic**, vary them by queue.
- **AutoWorkQueues:** "route the right interactions to the right reviewers. **Prioritise high-risk contacts.**"
- **Blended scorecards:** the AI handles the routine checks, people handle judgement.
- **Context Engine:** QA policies and compliance rules written in plain language, plus a knowledge base, plus a **testing console** to "try changes against real conversations before they go live. See exactly how a tweak affects scoring across your archive." **Tune it "until it's calibrated to your standard."**
- **Actions:** trigger workflows (coaching, **escalations**) the moment a score or compliance flag fires.
- **Coaching:** one-to-one sessions with a goal, e.g. *"Improve empathy from 3/15 to 12+/15"*, tied to evidence from the call.
- **Reason for contact:** query, complaint, enquiry or request, plus topic distribution and sentiment.
- **Reporting:** agent, **evaluator and calibration** performance, and a breakdown by line item.

### Recordsure (London; part of TCC Group) — [recordsure.com](https://recordsure.com/)
- **Create trusted data:** transcribes, classifies, dates and structures calls, documents and emails, "**preserving access to the original evidence**".
- **Check, score and explain:** completeness and process adherence. "**Findings connect back to the exact recording, transcript passage or document**."
- **Understand, decide and act:** "**direct experts to exceptions**", trigger workflows, and produce management reports that "stand up to scrutiny".
- Themes **colour-coded to the client's existing QA checklist**; every conversation gets a risk score.
- **Management reports broken down by product, adviser, client group and vulnerable customers**, which feed **their clients' Consumer Duty dashboards**. This is what a QA firm sends back to the bank.
- An **evidence pack** for each conclusion (marked-up documents).
- **Human–AI agreement** tracked as a headline figure (95%).

### Voyc (Amsterdam/UK; 100+ UK finance firms) — [voyc.ai](https://voyc.ai/), [customers](https://voyc.ai/customers)
- Reviews **every human and AI conversation**; flags **unhappy (complaint) and vulnerable** customers.
- "Accurate call grading against a **fully customisable script**, with **alerts triggered from keywords**" (Kingsbridge).
- Coaching: "**Find what your top performers do differently**"; managers see what each agent needs, "**with the conversation to prove it**".
- A **network effect**: "across 100M+ interactions in regulated finance, its patterns raise the bar".

### Aveni (Edinburgh; £23m+) — already covered in BUILD_PLAN §8
- Overrides **logged with a reason** and fed into the next release.
- Plain-language framework updates.
- Outlier detection.
- Coverage of the whole case.

## 4. What we take (only things they already sell) → Redress for a QA firm

**The setup on stage:**
- **Harbour Assurance** is a fictional outsourced QA firm.
- Its client is **Thistle Bank** (a second client, **Northwind Finance**, shows the multi-client idea).
- The user on screen is **a QA analyst at Harbour**.

| # | Taken from | Redress version | Demo moment |
|---|---|---|---|
| 1 | EvaluAgent auto QA scorecard + auto-fail | Each client has its own weighted scorecard, plus **FCA auto-fail items**: complaint not recognised · wrong deadline · vulnerability missed · promised an outcome | A call scores **65% FAIL · 1 auto-fail: vulnerability missed** |
| 2 | Recordsure evidence links | Every score links to the **exact transcript line** and the rule (DISP / FG21/1 / the client's policy) | Click "vulnerability missed" → *"I was in hospital"* highlighted at 00:42 |
| 3 | EvaluAgent AutoWorkQueues + Recordsure "experts to exceptions" | **Work queue**: high-risk and low-confidence calls go to an analyst; clean high-confidence calls auto-pass | 100 calls → **14 to an analyst, 86 auto-passed** |
| 4 | Aveni overrides with a reason + EvaluAgent calibration | **The analyst labels the call**: confirm or override each item, with one line of reason. This is the labelling you described. It becomes a playbook rule straight away and a Mubit training example. | Override → rule 7 → playbook v5 |
| 5 | EvaluAgent testing console | **"Test on the archive"**: re-run the new rule over last week's calls before it goes live, and show what changes | 6 calls change score, shown as before → after |
| 6 | Recordsure's 95% agreement figure | **Agreement meter**: AI vs analyst agreement per client, rising with each correction. **Above a threshold, a call type moves to auto-pass.** This is your "eventually it does it itself", and it's a real feature. | 78% → 91% → ships more calls to auto-pass |
| 7 | Recordsure reports for the client + EvaluAgent Actions | **The weekly client report emailed to Thistle's complaints manager (real Gmail)**: complaints the agents missed, vulnerable customers, agents to coach, with evidence links | The report lands on a phone |
| 8 | EvaluAgent coaching + Voyc "with the conversation to prove it" | Agents flagged for coaching, with the exact calls and a goal (*"Empathy 3/15 → 12/15"*) | Inside the client report |
| 9 | (ContactBabel + all of the above) | **100-tile wall**: the contract samples 2 calls; Redress reviews all 100 | The opening hook |

**Cut:** live voice agents, live call checks, pre-launch agent testing, CRM, sentiment, predictive metrics.

## 5. Why a QA firm wants Mubit (and owning the weights)

- **Margin.** A QA firm is paid per call reviewed. Moving the repetitive review from a big model to its own small model is the difference between offering 100% coverage and offering 2%. Measure the cost per 1,000 calls tonight.
- **One adapter per client.** Each bank's scorecard sits in its own Mubit task, so each bank gets its own adapter, **trained only on that bank's labelled calls. Nothing crosses between clients.** That's a confidentiality selling point. Each client's own task is "Thistle 25/25 → v2 passed; Northwind 12/25 collecting".
- **The labels become an asset.** Years of expert QA judgements become the firm's own model. Aveni spent 7 years building FinLLM; Voyc sells its "network" across 100M interactions. Redress gives a QA firm the same advantage, built from its own analysts' work.
- **If Mubit lets you take the weights (check this, see below), they can be reused:**
  - deploy the reviewer **inside a bank's own environment** for clients who won't let call recordings leave (EvaluAgent and Recordsure both sell "data stays in region / UK hosted");
  - **freeze a version for audit**: "this exact model version scored these calls in March" (Recordsure's "consistent, testable, auditable findings");
  - **train new analysts**: they score practice calls and compare their scores with the model, which is calibration practice;
  - **move between LLM vendors** without retraining the team's judgement.
- ⚠️ **Not verified yet:** Mubit's homepage says "Your frontier models stay. **You own what's built**," but the docs don't explain how to export an adapter. **Ask at office hours (RISKS M11).** Until then, say "you own what's built", not "download the weights".

## 5b. "AI QA already exists, so why Mubit?" (the question every judge will ask)

**Answer: today's AI QA is *configured*. Redress is *trained*, by the QA firm's own analysts, every day.**

**How today's tools work, from their own sites:**
- **(A) A rented big model plus prompts.** EvaluAgent: write "guidelines in plain language", add a knowledge base, "tune it until it's calibrated".
- **(B) The vendor's own specialist model.** Aveni's FinLLM took **7 years and a 100-billion-token corpus**, and overrides "feed the next assessment release" of *their* model.

**The gaps Mubit fills:**

| Gap | Today | With Redress + Mubit |
|---|---|---|
| **Analysts' corrections are wasted** | (A) logged for audit; the model doesn't learn. (B) they improve the vendor's model, on the vendor's schedule, shared with everyone. | Every correction becomes a **rule straight away** and a **training example for the firm's own model** |
| **100% coverage is expensive** | Every call is a long transcript through a frontier model. That's why Aveni built small models ("up to 25× cheaper", their claim), and it took 7 years. | Mubit turns the big model's corrected answers into a **small model for each task, built from the firm's own traffic**. No ML team needed. |
| **Each bank client is different** | One configuration per client on a shared model | A different scorecard per client means **a different Mubit task**, which means **one model per client, trained only on that client's labels** |
| **Scores drift when the provider updates its model** | A rented model changes under you | A **versioned** model that only changes when a new version passes Mubit's tests. Stable scoring for audit. |
| **Ownership** | Rented | "You own what's built" (Mubit's homepage). **Confirm export at office hours.** |

**Pitch line:** *"AI QA already exists. It's either a rented model you tune with prompts, or a vendor's model that took seven years to build. Redress gives a QA firm the second, built from its own analysts' corrections, through Mubit."*

**Prove it, don't claim it.** The Mubit beat shows the same 25 held-out calls in three rows:
1. the big model with the prompt only (= today's AI QA);
2. the big model plus the analysts' corrections (the playbook);
3. the firm's own model (the Mubit adapter, in Try models).

Columns: accuracy against the analysts' gold labels · latency · cost per 1,000 calls. Add a counter: *"37 corrections this week → 37 training examples."*

**Be honest if asked:**
- Today Mubit runs the adapter only in its console (Try models), not from our app.
- Corrections reach the model through corrected big-model answers, not a corrections API.
- Mubit doesn't help a small QA team with low volume and rules that never change. Admitting that makes the rest believable.

**About the statistics:**
- The adoption and agreement figures (95% agreement, 88 → 96%, 24 → 6 minutes) are **vendor-reported**. Quote them as "vendors report…", as proof the market buys this.
- The more independent figures: **QA samples 1–2%** and **only 10% of UK contact centres use AI for vulnerable customers** (ContactBabel survey); **about 75% of UK financial firms use AI somewhere** (Bank of England / FCA survey, cited by the FOS).

## 5c. Sampling and data split (settles the "only 5%" worry)

**Three different numbers that get mixed up:**

| Number | What it is | Ours |
|---|---|---|
| **Calls a human reviews** | Supervision: analysts confirm or override | About 5% |
| **Calls the model learns from** | Every call reviewed through Mubit, with the analysts' rules applied, can become a training example. **This is not 5%. It's every call.** | About 100% (minus held-out) |
| **Calls never used for training** | The test set, used only to measure accuracy honestly (`x-middleware-record: metadata`, set in code) | 25 of 100 in the demo |

**How to pick the 5% humans see. The teammate is right that a random 5% is wrong.**
- **About 4% targeted:** the AI's least confident and highest-risk calls (a possible complaint, vulnerability, an automatic fail). Those corrections teach the most. EvaluAgent ("prioritise high-risk contacts") and Recordsure ("direct experts to exceptions") both do this.
- **About 1% random:** an unbiased audit slice, so the agreement figure is honest and not inflated by only checking hard calls. **It never drops to zero**, because regulators want evidence.
- As agreement rises, the targeted share falls (more call types auto-pass). The random audit stays.

**Rare cases.** Complaints and vulnerable customers are a minority of calls. A model that mostly sees clean calls learns to say "clean".
- Make the synthetic warm-up set **about 40% hard cases**: hidden complaints, vulnerability mentioned in passing, wrong deadline.
- Turn each correction into about 10 variations.

**If someone means a 95/5 train/test split:** with 100 calls, 5 test calls is too few, because one mistake swings the score by 20 points. **Keep 25 held out.**
- Report results as counts ("23/25"), averaged over 3 runs.
- Mubit also holds back its own test cases from the training calls when it grades each version.

## 6. Demo (3 minutes, flashy beats only)

| Time | Beat |
|---|---|
| 0:00 | **"Thistle Bank sent us 100 calls this week. Our contract says we check 2."** The wall lights 2. **Redress reviews all 100**, and complaints, vulnerable customers and auto-fails light up. |
| 0:30 | **A real call.** Sultan (customer) rings you (Thistle agent) on speaker. You handle it badly on purpose. You hang up, the recording uploads, and **the scorecard appears in seconds: 65% FAIL, 1 auto-fail**, with the evidence line. |
| 1:10 | **The analyst's queue.** 14 high-risk calls. The analyst overrides one item with a one-line reason, then runs **Test on the archive**: 6 calls change. **The agreement meter goes up.** |
| 1:50 | **Mubit console**: Thistle's `call.review` **v2 passed**, side by side with the big model, and Northwind's task still collecting. *"One model per client, trained only on its own labels."* |
| 2:20 | **The client report** lands in Thistle's complaints manager's Gmail: 9 missed complaints, 7 vulnerable customers, 3 agents to coach, all with evidence. |
| 2:40 | **Money:** coverage 2% → 100% · analyst minutes per call · cost per 1,000 calls, big model vs our own model (measured). **Last line:** *"Every label your analysts make becomes a model you own."* |

## 7. What changes in the build (if you lock this)
- **One hero Mubit task per client:** `call.review` (Thistle). Northwind's task stays partial on purpose.
- Plus `rule.induce` and `report.draft`. All go through Mubit.
- **Call recording upload + speech-to-text with speakers separated** (Deepgram pre-recorded, `diarize=true`). No voice agent.
- **100 synthetic Thistle calls**: 75 practice (warm-up + wall), 25 held out (`metadata` only), plus 20 Northwind calls.
- **Gmail:** one sending account (Harbour Assurance) → the Thistle complaints manager's inbox, for the report.
- **Routes v3:** keep v1.1 minus the live, takeover, pre-flight and Ava-check routes. Add:
  - `POST /api/calls` (audio upload)
  - `GET /api/wall`
  - `GET /api/queue`
  - `GET /api/clients/{id}/agreement`
  - `POST /api/rules/test` (test on the archive)
  - `POST /api/reports/{client}/send`
  - plus `scorecard` and `auto_fails` fields on each case
