# Catch: the problem, where it came from, and the sources

**Straight answer: Catch did not come from a past hackathon win. I put it together from three things:**
1. what won at the finance hackathons we researched (narrow compliance jobs with a human signing off);
2. the venue (Canary Wharf);
3. what Mubit's judges need to see (a recurring task where a human fix visibly improves the model).

I then checked the market. Three funded companies already sell this. Two big UK lenders, Lloyds Banking Group and Nationwide, put money into one of them in 2026. That is stronger proof than a hackathon win. No hackathon winner I could find did exactly this.

Everything below links to where it came from. If a figure comes from the company selling the product, or from someone summarising a source, it says so.

---

## 1. The problem in plain English

A UK lender (a bank, credit card company, car finance firm or loan company) gets thousands of messages a day by chat, email and phone. Two things in those messages carry legal duties.

**1. Complaints.** Under the FCA's rules, a complaint is **any spoken or written expression of dissatisfaction, "whether justified or not"**, about a financial service, where the customer says or implies they lost money, were distressed, or were inconvenienced. ([FCA Handbook glossary, "complaint"](https://www.handbook.fca.org.uk/handbook/glossary/G197.html))
- The customer does **not** have to use the word "complaint". ([Law Brief guide to ombudsman claims](https://www.lawbriefpublishing.com/2025/05/free-chapter-from-a-practical-guide-to-financial-ombudsman-service-claims-second-edition-by-adam-temple-devon-airey/))
- Once it counts as a complaint, the clock starts. The firm must acknowledge it promptly. It must give a written answer within **8 weeks**, or **15 business days** for payment complaints. ([FCA Handbook DISP 1.6](https://handbook.fca.org.uk/handbook/DISP/1/6.html))
- After that, the customer can take it to the **Financial Ombudsman Service** (FOS), which charges the firm **£650 per case** it investigates. Most firms get 3 free cases a year. ([FOS budget 2025/26](https://financial-ombudsman.org.uk/files/324591/Financial-Ombudsman-Service-Plans-Budget-2025-26.pdf))

**2. Vulnerable customers.** The FCA expects firms to spot customers in vulnerable circumstances and treat them fairly. Its guidance, **FG21/1**, groups vulnerability into **four drivers: health, life events, resilience** (money buffers) **and capability** (understanding money). ([Forvis Mazars summary](https://www.forvismazars.com/uk/en/industries/financial-services/thought-leadership/fca-guidance-on-treatment-of-vulnerable-customers)) The Consumer Duty, in force since July 2023, makes this about outcomes, not just policies.

**Where it breaks.** Front-line staff and chatbots read "third time asking, nobody called me back" as a service request, not a complaint. They read "I've just been signed off work" as small talk, not a health and life-event flag. QA teams then check a small sample after the fact. Aveni, which sells a fix for this, says manual QA typically covers only 5–10% of interactions. That's their marketing figure, not an independent one. ([fintech.global](https://fintech.global/2026/09/11/aveni-closes-the-gap-between-isolated-checks-and-real-risk/))

**What Catch does.** It reads every message, flags complaints and vulnerability with the exact words that triggered each flag, and every fix a QA reviewer makes trains the firm's own model through Mubit.

---

## 2. The numbers (all sourced)

| Fact | Number | Source |
|---|---|---|
| Complaints UK firms received, Jan–Jun 2025 | **1.83 million** (revised from 1.85m) | [FCA aggregate complaints data 2025 H1](https://www.fca.org.uk/data/complaints-data/aggregate-complaints-data-2025-h1) |
| …of which banking and credit cards | **899,910**, up 7.2% | same |
| Complaints, Jul–Dec 2025 | **1.74 million** | [FCA 2025 H2](https://www.fca.org.uk/data/complaints-data/aggregate-complaints-data-2025-h2) |
| Redress firms paid, H1 2025 | **£283m** | FCA 2025 H1 |
| New cases at the ombudsman, 2024/25 | **305,726**, the most since the PPI scandal (2018/19) | [Mortgage Solutions on the FOS annual data](https://www.mortgagesolutions.co.uk/news/2025/07/02/fos-complaints-reach-highest-level-in-six-years-in-2024-25/) |
| …of which car finance commission | **73,328** | same |
| Ombudsman fee per case | **£650** (£680 proposed for 2026/27) | [FOS budget](https://financial-ombudsman.org.uk/files/324591/Financial-Ombudsman-Service-Plans-Budget-2025-26.pdf), [Mortgage Solutions](https://www.mortgagesolutions.co.uk/mortgage-news/2026/01/13/fos-lays-out-plan-to-up-fees-after-two-year-freeze/) |
| UK adults with signs of vulnerability | **26.4 million (49%)**, FCA Financial Lives 2024 | [Regulation Tomorrow](https://www.regulationtomorrow.com/2025/05/fca-financial-lives-2024-survey/), [Cover Magazine](https://www.covermagazine.co.uk/news/4413771/49-uk-adults-financially-vulnerable-fca) |

**How to say it on stage:** "UK firms log about 3.5 million complaints a year, and those are only the ones they recognise. Half of UK adults show signs of vulnerability. Every complaint a firm misses can end up at the ombudsman, at £650 a case."

---

## 3. Proof that firms get this wrong (real enforcement)

- **Volkswagen Financial Services UK, October 2024.** Fined **£5.4m** and agreed **£21.5m redress to about 110,000 customers** for failing to treat customers in financial difficulty fairly, 2017–2023. ([FCA press release](https://www.fca.org.uk/news/press-releases/fca-fines-volkswagen-finance-over-treatment-customers-financial-difficulty)) Write-ups of the final notice say that in some cases it also broke the complaint rules by **failing to identify complaints**. ([Ocorian](https://www.ocorian.com/fca-fines-volkswagen-financial-services-ps54m-failing-customers-financial-difficulty), [Mishcon de Reya](https://www.mishcon.com/news/financial-conduct-authority-issues-final-notice-imposing-a-5397600-financial-penalty-on-volkswagen-finance)) Read the final notice itself before quoting the exact rule.
- **TSB.** Fined **£10.9m** over customers in financial difficulty. ([FCA](https://www.fca.org.uk/news/press-releases/fca-fines-tsb-over-treatment-customers-financial-difficulty))
- **The FCA's vulnerability review, March 2025.** It found progress but gaps, especially for customers with several vulnerabilities. A law-firm summary reports that most firms couldn't properly monitor outcomes for vulnerable customers. ([Covington](https://www.cov.com/en/news-and-insights/insights/2025/04/fca-publishes-findings-on-firms-treatment-of-consumers-in-vulnerable-circumstances), [A&O Shearman](https://finreg.aoshearman.com/FCA-publishes-findings-from-review-of-firms-tre))
- **The FCA's Consumer Duty complaints review of 40 firms** questioned how well firms' oversight, reporting and root-cause work actually functions. ([Ocorian](https://www.ocorian.com/knowledge-hub/insights/fca-consumer-duty-complaints-review-key-findings-governance-mi-and-reporting))
- **The same failure happens abroad.** The Central Bank of Ireland found firms failing to identify complaints "at the earliest opportunity", often acting only once the customer used the word "complaint". This is Ireland, not the UK, so it's supporting evidence only. ([Credit Strategy](https://www.creditstrategy.co.uk/news/fca-warns-of-enforcement-action-over-complaints-policies-3788))

---

## 4. Who already sells this (the market proof)

| Company | What it does | Proof it's real |
|---|---|---|
| **Aveni** (Edinburgh) | Aveni Detect checks calls, emails and chats for complaints and vulnerability, using its own finance-trained model (FinLLM). Aveni says FinLLM is about 25 times cheaper than general models for this work. That's their claim, not an independent one. | **£11m Series A in 2024**, then **£12m in 2026** with **Lloyds Banking Group and Nationwide** investing. ([Scottish Financial Review](https://scottishfinancialreview.com/2026/06/04/aveni-edinburgh-ai-wealth-startup-raises-12m/), [Aveni](https://aveni.ai/blog/aveni-launches-enhanced-detect-to-provide-complete-case-level-outcome-testing-across-every-customer-interaction/)) |
| **NICE** (big contact-centre software company) | "Enlighten AI for Vulnerable Customers" checks every interaction against the FCA's vulnerability drivers and complaints | Won AI Solution of the Year at the 2023 National Technology Awards ([Call Centre Helper](https://www.callcentrehelper.com/nice-receives-ai-solution-of-the-year-award-226443.htm)) |
| **Voyc** (Amsterdam) | Flags complaints and vulnerable customers across 100% of monitored calls | **$2m seed, May 2025** ([Silicon Canals](https://siliconcanals.com/dutch-based-voyc-raises-e1-7m-in-seed-funding/), [Crunchbase](https://crunchbase.com/organization/voyc-ai)) |

**What this means for you:** the problem is real and paid for. Lenders are investing in it. **Your difference** has to be the Mubit angle. Their public pitch is a ready-made model built for finance. I haven't checked whether they also train one per client, so don't say they don't. Catch's pitch is that each firm's own QA fixes become that firm's own model, refreshed when the rules change.

---

## 5. Why "own your model" is a genuine argument here (Track 2)

- **Vulnerability data is often health data.** In March 2026 the FCA and the data regulator (the ICO) issued a joint statement. It says firms "may need to process special category data" when handling vulnerability, and gives health data as the example. That needs an extra legal condition (UK GDPR Article 9), and sharing it with a third party needs contracts in place. ([FCA/ICO joint statement](https://www.fca.org.uk/publications/corporate-documents/joint-fca-and-ico-statement-regulatory-expectations-regarding-firms)) A firm that runs this on a model it owns, hosted where it chooses, has a much simpler data story than one sending every message to a closed US model.
- **Volume.** The 3.5 million complaints a year are only the ones firms recognise. Screening *every* message means far more calls. At that volume, cost per message decides whether you can check 100% or have to sample 5%.
- **The rules keep moving.** Car finance commission alone brought 73,328 ombudsman cases in 2024/25. The FCA's compensation scheme for it has changed several times, and in June 2026 parts were paused after a legal challenge. ([Paul Hastings](https://www.paulhastings.com/insights/client-alerts/update-fca-confirms-motor-finance-redress-scheme-key-points-for-motor-finance-lenders)) That is the "fast refresh" track in real life.

---

## 6. Hackathon validation, honestly

**No past winner did exactly this.** I searched:
- **FCA TechSprints.** A Consumer Duty TechSprint ran in July 2023 ([techUK](https://www.techuk.org/resource/financial-conduct-authority-s-consumer-duty-techsprint.html)) and a Financial Inclusion TechSprint in 2024, but neither published named winners.
- **UK bank hackathons.** The NatWest × Google Cloud hackathon at Edinburgh was won by "Finny AI", a savings companion, not this. ([University of Edinburgh](https://www.business-school.ed.ac.uk/about/news/nextgenhack))
- **Indian bank hackathons.** They were all about fraud.

**Close winners from 2025–2026 (the same kind of problem):**

| Winner | What it did | Why it's validation |
|---|---|---|
| **Claimsio**: 2nd at ElevenLabs Warsaw 2025, and a top winner at the **MAS Global FinTech Hackcelerator 2025** | AI-native debt collection that stays inside the rules | The closest match. It's collections compliance, and almost all the fines above are about customers in financial difficulty. ([ElevenLabs](https://elevenlabs.io/blog/announcing-the-winners-of-the-elevenlabs-worldwide-hackathon), [Fintech News SG](https://fintechnews.sg/?p=121960)) |
| **CIBC**: **Gold at DTCC Innovate AI 2025** | AI that reads regulatory updates and works out what applies to the bank | Compliance automation won the top prize at a big finance hackathon ([DTCC](https://www.dtcc.com/dtcc-connection/articles/2025/april/02/dtcc-announces-winners-from-first-ai-powered-hackathon)) |
| **NovaMind (Deutsche Bank)**: Silver at DTCC 2026 | Handles post-trade exceptions with an audit trail | Back-office work with human review ([DTCC 2026](https://www.dtcc.com/dtcc-connection/articles/2026/march/26/innovate-dtcc-2026-industry-powered-ai-hackathon-winners)) |
| **VendorGuard**: 1st at Microsoft Agent Academy 2026 | Rates contract clauses red, amber or green against 15 rules | A compliance classifier with clear labels ([Microsoft](https://devblogs.microsoft.com/powerplatform/agent-academy-hackathon-winners)) |

**The pattern:** finance judges keep rewarding narrow compliance jobs with a human signing off and a saved-money number. Catch fits that pattern, and no winner has taken this exact spot yet.

---

## 7. You don't need a finance person to label the data (but you do want one for the pitch)

The definitions are public rules, so anyone can label with this checklist.

**Is it a complaint?** Yes only if all three are true:
1. The customer is unhappy about something the firm did or didn't do. They don't have to say "complaint".
2. It's about a financial product or service.
3. They say or imply lost money, distress, or real inconvenience.

**Is the customer vulnerable?** Tag any that apply:
- **Health:** illness, disability, mental health ("signed off work", "in hospital", "my anxiety").
- **Life event:** bereavement, job loss, divorce, new baby, caring for someone.
- **Resilience:** can't absorb a shock ("can't make Friday's payment", "overdrawn till payday").
- **Capability:** struggles with money, language or digital ("I don't understand this letter", "my son usually does this").

**Recruit target, by 21:30.** Find someone in the room who has worked in complaints handling, contact-centre QA, conduct risk or compliance at a UK bank, lender, insurer or fintech. It's Canary Wharf with 500 builders, so ask in #find-a-team on Discord too. Ask them three things:
1. "Do agents miss complaints in chat or email? How do you find them now, and what share gets checked?"
2. "When QA finds a missed complaint, what happens next?"
3. "Would a model trained on your own QA team's fixes be useful?"

Then get **one sentence you can quote, with their name and role**. If nobody turns up, the build still works because the labels come from the rulebook. The pitch just loses its expert voice.

---

## 8. Judge questions and answers

| They ask | You say |
|---|---|
| "Isn't this Aveni / NICE?" | "They're proof that lenders pay for this. Their pitch is a ready-made finance model. Ours is that *your* QA team's fixes become *your* model, updated when the rules change. With Mubit you start on a closed model on day one and move to a model you own." |
| "Why not just write a better prompt?" | "We do that too: fixes work straight away. But at bank volume, and with health data counted as special category data under the March 2026 FCA/ICO statement, you want that behaviour in a model you own. Here's the cost and speed side by side." Use measured numbers. |
| "How do you know your labels are right?" | "They follow the FCA's own three-part complaint definition and the four vulnerability drivers in FG21/1. The test set was never used in training." Add your recruited expert's check if you got one. |
| "What about false alarms?" | "A flag only sends the message to a human, which is cheap. A miss is expensive: £650 at the ombudsman, plus redress, plus a rule breach. We tune to miss as little as possible and show the false-alarm rate too." |
| "Is this automated decision-making under GDPR?" | "No decision is made about the customer. Catch sends messages to a human reviewer." (UK GDPR Articles 22A–22C cover decisions made *solely* by automation that have significant effects.) |
| "Where's the data from?" | "Synthetic messages we wrote and labelled. Mubit records content, so no real customer data went anywhere." |

---

## 9. The honest trade-off with Vokal

- **Catch:** easy for judges to follow, strong money story, all three tracks. You're borrowing a domain, so the expert quote matters.
- **Vokal v3:** your own domain and your own research. Recent winners did the same thing (Gem-Care). The money ending is weak.

If finance still feels too foreign after reading this, Vokal is a legitimate choice, not a step down.
