# Catch: what it does, what we take from Aveni, and the demo

**Short version:** Catch doesn't just sort emails. It listens to calls and reads every chat and email as they come in, then:
- catches the complaints and vulnerable customers that staff miss;
- acts on them straight away;
- learns from every override a reviewer makes.

Sorting into the right team is one of five things it does.

---

## 1. What Catch actually does

For every incoming call turn, chat or email at "Northwind Finance", a fictional UK lender:

| Step | What happens | Who sees it |
|---|---|---|
| 1. **Read** | The message, or the last few turns of a live call, goes to Catch's one Mubit task | — |
| 2. **Decide** | Is it a complaint under the FCA rules? Which of Northwind's 8 complaint categories? Any of the four vulnerability types (health, life event, resilience, capability)? | — |
| 3. **Show evidence** | The exact words that triggered each flag get highlighted | Everyone |
| 4. **Act** | Opens a complaint case and **starts the 8-week clock** (15 business days for payment complaints). Sends it to the right team (Complaints, Financial Support, Bereavement). **During a live call it prompts the agent** with what to say. Drafts the acknowledgement letter. | Agent, complaints team |
| 5. **Learn** | A QA reviewer overrides a wrong call and gives a reason. The fix works on the next message straight away and goes into the next version of Northwind's own model through Mubit. | QA reviewer |

**Three people use it:**
1. **The frontline agent:** live prompts during a call.
2. **The QA reviewer:** checks the flags and overrides wrong ones with a reason.
3. **The complaints manager:** open cases, clocks running out, new trends.

---

## 2. Aveni teardown: what they sell and what we take

Taken from Aveni's own public pages: [home](https://aveni.ai/), [Detect](https://aveni.ai/compliance/detect/), [Assure](https://aveni.ai/compliance/assure/), the [vulnerability guide](https://aveni.ai/blog/consumer-duty-vulnerability-detection-requirements-tools/) and [fintech.global, Sept 2026](https://fintech.global/2026/09/11/aveni-closes-the-gap-between-isolated-checks-and-real-risk/).

**What they sell**
- **Detect:** reviews 100% of conversations after they happen, using the firm's own rules.
- **Assure:** watches AI agents live, using a quick scan on every reply and a deeper check on anything risky. It can block, redact or escalate mid-conversation. (Beta.)
- **Approve:** tests chatbots and AI agents before they go live. (Beta.)
- **Assist** and **File Check:** paperwork and file reviews for financial advisers.
- **The models underneath:** FinLLM (their own), 150+ smaller specialist models, plus OpenAI, Anthropic and Google models.

**Their numbers (their own claims, unverified):**
- 250+ firms as customers, including Lloyds Banking Group, Nationwide and Quilter;
- 1.6M conversations assessed by Detect;
- £4.0M a year saved by firms that stopped manual sampling;
- manual sampling covers 5–10% of conversations;
- 25× cheaper than general-purpose models on complex cases.

### What we take for the hackathon

| Aveni feature | Catch version | Keep? |
|---|---|---|
| Checks 100% of conversations, no sampling | Every message and every call turn goes through Catch | **Must** |
| Evidence citations | The trigger words highlighted, plus the rule behind the flag (the FCA complaint definition, or one of the four vulnerability types) | **Must** |
| Reviewer can override, every override logged with who, what and why | Override button with a required one-line reason, and an audit log | **Must**, and this is our wedge (below) |
| Automatic case typing: right case type, owner and template | Opens the case, starts the 8-week clock, sends it to the right team | **Must** |
| Real-time intervention mid-conversation (Assure) | A live prompt to the agent during the call: "Log this as a complaint. Say: '…'" | **Must** (this is the voice feature) |
| Quick scan on every turn, deeper check only when risky (Assure) | The architecture slide: Northwind's own small model scans every turn, and the big model only handles flagged ones. **This is the clearest reason for Mubit.** | Pitch it, build it if there's time |
| One case across call, email and chat | Sarah's call yesterday and email today, shown as one case, using our own case ID. Don't use Mubit's `session_id`: it needs OpenAI's `store=true` (RISKS M16). | Should |
| Trend analysis and outlier detection | One tile: "New this week: car finance commission, up 4×" | Should, and it sets up the rules-changed beat |
| "Update without rework" when policies change | Fix 3 messages and the model catches the new category | Should |
| Coaching, board dashboards, CRM sync, pre-launch testing (Approve) | — | **Won't** (no time) |

### Our wedge (corrected 21:25)
~~Their public pages don't mention learning from overrides.~~ **Wrong.** Aveni's File Check page says "every override is logged and feeds the next assessment release." Say this instead:
> "Aveni proved the workflow. Their overrides feed the next release of *their* model. Ours change the next call straight away and the bank's *own* model overnight, through Mubit."

See BUILD_PLAN.md §8 for the full list of what we take from Aveni.

---

## 3. Voice: how calls fit in

**Recommended setup: a live call into the same Mubit task.** Calls, chats and emails all go to **one Mubit task**, with the channel noted in the user message. That's good for Mubit too, because a single call produces a dozen classifications. That's a dozen examples, so we reach the training threshold faster.

```
Phone (Sarah)                        Laptop on the projector (Northwind agent console)
"Call Northwind" page  --audio-->  backend --> speech-to-text (live)
                                       |
                                       +-- each customer turn + last 6 turns --> Mubit task (classify)
                                       |                                           |
                                       +<-- flags + quote + category + nudge -------+
                                       --> live transcript, flags, agent prompt, case opened
```

- **Speech-to-text:** Chrome's built-in speech recognition, or Deepgram, streaming. Speech-to-text isn't an LLM call, but confirm the rule with Max (risk V2). Every classification and every prompt to the agent goes through Mubit.
- **No phone number.** Sarah uses a browser page on a teammate's phone. A real Twilio number is a stretch goal only (risk V5).
- **Fallback:** a pre-recorded Sarah call played through the same pipeline (risk V1).
- **Later, not tonight:** watching an AI voice agent the way Aveni Assure does. Mention it as the roadmap.

---

## 4. The demo, scene by scene (3:00 target)

**Setup:** the laptop on the projector shows the Catch console. A teammate holds a phone showing "Northwind Finance — Call us". You present. A second browser tab has the Mubit console open and logged in.

**Keys:** `L` drops in the next scripted message · `G` jumps to the money screen · `R` resets everything.

| Time | Scene | On screen | You say (customer moments and money only) |
|---|---|---|---|
| 0:00 | **Hook** | A dark screen, then the Catch console | "UK lenders logged 3.5 million complaints last year, and those are only the ones they noticed." |
| 0:10 | **The live call** | The teammate taps Call and speaks as Sarah: *"Third time I'm calling, nobody rang me back like you promised. And I've just been signed off work, I don't know how I'll make Friday's payment."* The transcript scrolls live. About 2 seconds later: 🔴 **COMPLAINT**, with "nobody rang me back like you promised" highlighted. 🟠 **VULNERABLE: health, resilience**, with "signed off work" and "make Friday's payment" highlighted. | Stay silent and hold for 3 seconds. Then: "Under FCA rules that's a complaint, even though Sarah never used the word. And she's a vulnerable customer." |
| 0:40 | **It acts** | The agent prompt card: *"Log as complaint. Tell Sarah she'll get a written response within 8 weeks. Offer a payment plan conversation and transfer to Financial Support."* Case #1042 opens, the clock shows its due date, and the case goes to Financial Support. | "The agent gets told what to say while Sarah is still on the line. The case is open and the clock is running." |
| 1:00 | **The miss** | Press `L`: an email arrives. *"Fine, I'll pay the £12 late fee AGAIN even though your app was down."* Catch marks it **not a complaint**. | "Here's one it gets wrong." |
| 1:10 | **The override** | Priya (QA reviewer) clicks Override → complaint, category Fees & charges. Reason: *"Blames our outage for the fee: unhappy and lost money."* The audit log shows the change. | "Priya fixes it in one click and writes one line saying why." |
| 1:25 | **Instant** | Press `L`: *"App crashed again so I got charged, brilliant."* It's caught, with "learned from Priya's fix, 2 minutes ago". | "Her fix works on the very next message." |
| 1:40 | **Permanent (Mubit)** | Switch to the Mubit tab. The **Tasks** page shows the kept-example count. **Adapter history** shows version 1 *Below target* and version 2 *Passed*. **Try models**, side by side on the same message: the big model on the left, Northwind's own model on the right. Same answer, with the response time for each shown. | "Every override Priya made this week trained Northwind's own model. Mubit tested it against the big model before switching." |
| 2:15 | **The rules change** | Back in Catch, the trend tile shows "New: car finance commission, up 4×". Version 2 misses *"did the dealer get paid commission on my car loan?"*. Priya fixes 3, and version 3 catches it. | "When the rules move, Northwind's model moves with them." Say plainly that version 3 trained at 06:00 from those exact fixes. |
| 2:40 | **Money screen** (`G`) | 200 test messages Catch has never seen. Missed complaints by version: big model with prompt only → v1 → v2 → v3. Cost to screen 1 million messages: big model vs Northwind's own model, **measured tonight**. Share of conversations checked: 100% vs a 5–10% sample. | **Scripted last line:** "Every override Priya makes stops being an audit note. It becomes a model Northwind owns." |

**Expo version (30-second loop, no talking):** the live call clip (recorded) → flags → override → Mubit version 2 *Passed* → money screen, looping. A one-line card sits next to the laptop: *"Catch: every QA override trains your own complaints model."*

**What's live and what's prepared**

| Live | Prepared ahead (and we say so) |
|---|---|
| Sarah's call: real speech-to-text and real Mubit calls | Version 1 and version 2 trained overnight from our real corrections |
| The override and the instant fix | Version 3 trained at 06:00 |
| Every classification goes through Mubit | Test-set results computed at the 08:00 freeze |
| Try models side by side (one adapter start) | Screen recordings of every Mubit console beat, as a backup |
