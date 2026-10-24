# How call QA works in UK finance, and why we picked it

Research for Redress, Saturday 24 October, around 22:30. Every claim links to its source. **Vendor figures are marked as vendor figures.** They show what the market buys, not independent truth.

**In short:**
- QA analysts **listen to whole call recordings** for a tiny random sample (often under 2%).
- They score each call on a **weighted form with auto-fail items** (complaints, vulnerability, misleading statements).
- They **meet monthly to align their scoring**.
- Their findings become **coaching, urgent escalations, and the reports that feed the bank's Consumer Duty board report**.

Calls are the most expensive thing to check and the least-checked, so that's where AI and Mubit help most.

---

## 1. Can a bank do its own QA, or must it be a third party?

**Either.** Outsourcing is allowed, but "your firm is responsible and accountable… firms cannot delegate any part of this responsibility to a third party" ([FCA](https://www.fca.org.uk/firms/outsourcing-and-operational-resilience)).

What **is** required is **independence**. The compliance function must "operate independently", and "the relevant persons involved in the compliance functions must not be involved in the performance of the services" they monitor ([FCA Handbook SYSC 6.1](https://www.handbook.fca.org.uk/handbook/SYSC/6/1.html)).

| In-house examples | Outsourced examples |
|---|---|
| United Trust Bank's QA Manager uses Voyc ([Voyc](https://voyc.ai/customers)) | **TCC Group**: outsourced compliance, QA & oversight, complaints and remediation; 4,000+ regulatory engagements ([TCC](https://recordsure.com/tcc-group/)) |
| A major UK retail bank runs QA on 5,000 mortgage calls a month with Recordsure ([case study](https://recordsure.com/case-studies/improving-oversight-and-quality-assurance-across-mortgage-advice-conversations/)) | **Huntswood**: 280,000+ complaints a year for UK financial services, 139,000+ of them banking ([Huntswood](https://www.huntswood.com/?p=79717)) |
| Key Group: "multiple lines of defence" review calls ([Aveni](https://aveni.ai/blog/case-study-with-key-group/)) | **KPMG** runs complaint handling for clients with QA built in ([KPMG](https://kpmg.com/uk/en/services/consulting/managed-services/complaint-handling.html)) |

**Our customer is the outsourced QA firm.** One firm serves several banks, it's paid per review, and its analysts' labels are its asset. The same product works for an in-house QA team.

---

## 2. What QA analysts check on a call

Aveni's guide for UK financial services QA lists these as the things reviewers look for ([Aveni](https://aveni.ai/blog/prioritise-high-risk-calls-qa-review/)):

| Area | Examples |
|---|---|
| **Customer vulnerability** | Financial difficulty, bereavement, health, low resilience, difficulty understanding, life events |
| **Complaints and dissatisfaction** | Formal complaints, plus early signs like *"Nobody told me that would happen"* |
| **Potential customer harm** | Affordability, collections with customers in serious difficulty, misunderstood information, pressure, **incorrect statements** |
| **Process and control failures** | **Missing disclosures**, **incomplete checks**, incorrect information, **failure to recognise vulnerability**, **poor complaint handling**, not following support processes |

**Risk tiers, from the same guide:**

| Tier | What it covers | Response |
|---|---|---|
| **Critical** | Serious harm or urgent vulnerability | Immediate investigation and escalation |
| **High** | Complaints, significant vulnerability, material control failures | Prioritised human review within an agreed time |
| **Medium** | Repeated dissatisfaction, unclear understanding | Reviewed after critical and high |
| **Low** | Minor slips | Routine QA or coaching |

The FCA "does not prescribe a fixed percentage of customer calls that firms must manually review" (same source).

**What a scorecard looks like:** "a header, weighted criteria, a comments box, and a final percentage" ([Outsource Accelerator](https://outsourceaccelerator.com/glossary/qa-evaluation-sheets)). EvaluAgent's example scores Greeting 10/10 · Verification 15/15 · Empathy 3/15 · Resolution 7/15, giving **65% FAIL**, with a count of auto-fails ([EvaluAgent](https://www.evaluagent.com/auto-quality-assurance/)).

### Our Thistle Bank scorecard (built from the above)

| # | Item | Type | Rule |
|---|---|---|---|
| C1 | Complaint recognised and logged, even if the word "complaint" wasn't used | **Critical (auto-fail)** | FCA DISP definition of a complaint |
| C2 | Vulnerability recognised and support offered | **Critical** | FCA FG21/1 (health, life events, resilience, capability) |
| C3 | No promise of an outcome and no misleading statement | **Critical** | Consumer Duty: consumer understanding |
| C4 | Identity checked before account details were discussed | **Critical** | Data protection / Thistle security policy |
| S1 | Next steps and the right deadline explained (8 weeks, or 15 business days for payments) | 20 pts | DISP 1.6 |
| S2 | Checked the customer understood | 20 pts | Consumer Duty: consumer understanding |
| S3 | Information given was accurate | 20 pts | Thistle policy |
| S4 | Empathy and tone | 20 pts | Thistle service standard |
| S5 | Took ownership and agreed a follow-up | 20 pts | Thistle service standard |

---

## 3. How call QA happens today (the real workflow)

1. **Calls are recorded** in the contact-centre system (NICE, Genesys, Five9 and others).
2. **A random sample** is picked:
   - "**Traditional QA samples just 1–2% of interactions**" (ContactBabel survey of 200+ UK contact centres, [ContactBabel](https://www.contactbabel.com/?p=12967)).
   - Key Group reviewed **under 1%** of 3,000 interactions a month ([Aveni](https://aveni.ai/blog/case-study-with-key-group/)).
   - Most centres do **4–8 evaluations per agent per month**; about 60% do at least 5 ([Stealth Agents](https://stealthagents.com/research/bpo-quality-monitoring-workload-benchmarks-2026), citing SQM).
3. **An analyst listens to the whole call.** "The existing process relies on random sampling and human assessors listening to the full call" ([Key Group, via Aveni](https://aveni.ai/blog/case-study-with-key-group/)). Advice calls run about 90 minutes. One audit took **24 minutes** before automation ([EvaluAgent](https://www.evaluagent.com/auto-quality-assurance/), vendor figure). A transcript is optional. Speech analytics may provide one, but traditionally it's the audio.
4. **They score the scorecard** (yes / no / not applicable per item), write comments, and mark auto-fails.
5. **Calibration:** analysts score the same calls independently, then meet to agree.
   - 44% of teams do this monthly; 59% of sessions last an hour.
   - Tolerance is about 5 points between scorers.
   - Sources: [JustCall](https://justcall.io/blog/calibration-process-in-call-center.html), [Stealth Agents](https://stealthagents.com/research/bpo-quality-assurance-scorecard-benchmarks-2026), citing a QATC survey.
6. **What happens next:**
   - **The agent gets coaching** from their team leader.
   - **Critical findings are escalated** immediately. A missed complaint has to be logged and handled; a vulnerable customer is followed up.
   - **Management reports** go to the client or the board.

**The pain:** "reviews were at times inconsistent and uncoordinated across the organisation" (Key Group). In other words, calls are slow to review, hardly sampled, and analysts disagree with each other.

---

## 4. Is there a report at the end? Yes. It's required upstream

- **Consumer Duty board report.** Each firm's board must get a report on the results of its outcome monitoring, plus the actions taken (PRIN 2A.8). The FCA's review of these reports praised:
  - "quality assurance on at least 20 cases per month";
  - **"monitored third-party administrator calls with dates and ratings"**;
  - root-cause analysis of complaint trends;
  - outcomes tracked for **vulnerable customers**;
  - actions that are "specific and measurable" with a clear owner.

  It criticised reports with no evidence that actions worked ([FCA](https://www.fca.org.uk/publications/good-and-poor-practice/consumer-duty-board-reports-good-practice-and-areas-improvement)).
- **Outsourced QA firms send reports to their clients.** A UK consultancy doing managed reviews uses Recordsure to produce management reports "by product, adviser, client group and vulnerable customers", which feed its clients' Consumer Duty dashboards ([case study](https://recordsure.com/case-studies/document-intelligence-consultancy-managed-services-uk/)).
- **QA tools report on agents and on the evaluators themselves:** "agent, evaluator, and calibration performance… line item analysis" ([EvaluAgent](https://www.evaluagent.com/auto-quality-assurance/)).

**So the chain is: review → findings → client report → the bank's board report.** Writing that client report is a second recurring task. That's why Redress gives it **its own Mubit task per bank** (see [ARCHITECTURE.md](ARCHITECTURE.md)).

---

## 5. Why calls, and not files, emails or other QA

| Reason | Evidence |
|---|---|
| **Calls are the least-checked thing in finance** | 1–2% sampled (ContactBabel); under 1% at Key Group; a bank's mortgage calls were under 5% before AI (Recordsure) |
| **Calls are the most expensive to check** | You have to listen in real time. Advice calls run about 90 minutes; an audit took 24 minutes (vendor figure) |
| **Vulnerable customers use the phone** | **80% of people with care needs and 76% with health vulnerabilities have avoided online customer service** because it's hard to use (CCMA 2026 survey of 2,000 UK adults, as reported in search results. **Check the primary CCMA source before quoting on stage.** Related: Ofcom found vulnerable customers' phone outcomes "highly dependent on the member of staff", [Ofcom](https://www.ofcom.org.uk/research-and-data/multi-sector-research/accessibility-research/phone-broadband-pay-tv-vulnerable-customer-experiences)) |
| **Customers rarely say "I'm vulnerable"** | "Customers rarely self-identify as vulnerable", so it has to be heard in what they say ([Aveni](https://aveni.ai/blog/consumer-duty-vulnerability-detection-requirements-tools/)) |
| **The FCA asks for call monitoring** | Board-report good practice explicitly mentions monitoring calls (FCA, above) |
| **It's the clearest Mubit fit** | Huge volume, the same structured job every time, and expensive on a big model. That's exactly what Mubit's small adapters are for |
| **It makes the best demo** | A real call, hang up, and a scorecard appears in seconds. Files can't do that live. |

**Other QA (advice files, complaint files, KYC files) is the obvious next step for the same engine.** But it's already well served (Aveni File Check, Recordsure Document Intelligence), and it's worse on stage.

---

## 6. How the labelling should look in the demo (copying real life)

The analyst sees **the same evaluation form they use today, already filled in by the AI.**

- Each scorecard row shows:
  - the AI's answer (yes / no / not applicable);
  - **the quote with a timestamp** (click it to play the audio from that moment);
  - the rule;
  - the confidence.
- The analyst either **✓ agrees** or **changes the answer, and must give a one-line reason** when overriding. That reason is what `rule.induce` turns into a rule.
- **Critical fails** are pinned at the top. The **total score** recalculates live.
- There's a **comments box**, then **Submit evaluation**.
- There's a **calibration view**: the AI is treated as one more evaluator and its agreement with the analysts is tracked **per scorecard item**. That's the monthly calibration meeting, every day.

## 7. AI and analyst disagreements at scale

| Problem | Handling (copied from what the market does) |
|---|---|
| The AI can't be checked on every call | **Risk-ranked queue** (critical → high → medium → low) plus **low-confidence calls** go to analysts. **A random ~1% audit** keeps the agreement figure honest. |
| An analyst's insight only fixes one call | Their override becomes a **rule**, which is **re-run on the archive** (EvaluAgent's "testing console") and **applied to every future call**. One insight, applied everywhere. |
| When can we trust the AI on its own? | **Agreement per item.** When an item stays above a threshold (e.g. 95% over the last 50 audited calls), it's auto-accepted. Items below stay with humans. This mirrors how a new evaluator is calibrated. |
| The bank or agent disputes a score | The dispute goes back to an analyst, and their decision becomes another correction |
| "Is 100% right?" | **100% means 100% scored, not 100% correct.** Accuracy is measured on the random audit and shown in the client report. |
