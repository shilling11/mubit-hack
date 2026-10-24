# Catch: risk log

**The three risks that can sink the demo, all settled before 21:30:**
1. ~~Can Mubit train on a human's corrected answer? (M1)~~ **Answered: no API for corrections.** We use rules in the user message instead (see M1).
2. Is the task hard enough that the big model gets it wrong? (C1)
3. **Has anyone on the team seen an adapter actually train and pass?** Not yet: Redline's checklist item 9 is still unticked. How many trainings do we get tonight? (M3)

Everything else has a fallback.

> **Update 20:30:** the `bank` branch README (§3) has written answers from the Mubit team, gathered while the team built Redline. Those settled M1 and M2 and added M14–M19 below. **The team's `bank` branch is building Redress**, which is the same problem as Catch. These risks apply to it unchanged.

Status: 🔴 open and could kill the demo · 🟠 open with a fallback ready · 🟢 settled. Change the status as answers come in. Put a name in the owner column.

---

## Questions for the Mubit team at office hours (go now)

1. ~~Can a corrected answer become the training target?~~ **Answered by the Mubit team: no API for corrections. A Bad rating doesn't remove a call from training. Only `x-middleware-record: metadata` keeps a call out of training.**
2. ~~Can our app call a trained adapter?~~ **Answered: no model ID and no routing. Adapters only run in Try models.**
3. Is there an API for task and adapter status (kept examples, training state, test result)? Probably not, but nobody has asked.
4. How long does one training take? What are the daily training limit and the pause between trainings? Can they be raised for our project until 10:30 Sunday?
5. Try models gives 3 adapter starts per day. Can that be raised for judging day? Does a started adapter stay warm?
6. What does an adapter cost to run per million tokens, roughly? We need it for the cost-per-million-messages screen.
7. Can a firm export or host the adapter itself? This decides whether our data-privacy argument holds.
8. Audio: does `/openai/v1/audio/transcriptions` pass through Mubit with our own key? Does speech-to-text count as an "LLM call" under the rule that every LLM call goes through Mubit?

**Ask the organisers (Max on Discord):** how long the stage demo is and how long the expo slot is, what exactly "submit" means, and whether speech-to-text has to go through Mubit.

---

## A. Mubit risks (these would hit any idea, Vokal included)

| # | Risk | Why it matters | How we find out, and by when | Fallback | Status | Owner |
|---|---|---|---|---|---|---|
| M1 | Adapters copy the provider model's answers, and **there's no corrections API** (confirmed by the Mubit team). | "A correction turning into a model update" is 25% of the score. | ✅ Settled | **This is how we do it:**<br>1. A handler's correction plus their reason becomes a rule (a `rule.induce` call), which goes into the playbook.<br>2. The playbook goes in the **user message** of every later call.<br>3. The big model then answers correctly, those calls are recorded in full, and the adapter learns from them.<br>4. Base and held-out runs are sent as `metadata` only, so uncorrected answers never train.<br>On stage, say it straight: "the rule works straight away, and Mubit builds it into a small model." | 🟢 | |
| M2 | No model ID and no automatic routing. The adapter only runs in Try models (confirmed by the Mubit team). | The "after" shot lives in Mubit's console, not our app. | ✅ Settled | A second browser tab on Try models, with the full user message ready to paste (Try models only adds the system prompt). Screen-record it at the freeze. | 🟢 | |
| M3 | Unknown daily training limit, pause between trainings and training time. The limit resets at **01:00 BST tonight** (00:00 UTC). **Nobody on the team has seen an adapter pass yet.** | With one training a day we get version 1 and version 2, and the version 3 "rules changed" beat is impossible. If nothing passes, there's no model update to show. | Office hours Q4, **now**. Check Tasks → Adapters every hour after the warm-up script runs. | Start version 1 before 00:45 and version 2 after 01:00. If there's no version 3, show the rules change through the playbook only. If nothing passes, show the Tasks page progress and say so honestly. | 🔴 | |
| M4 | Version comes back "Below target" (the small model doesn't match the big one's answers well enough). | No passing adapter means nothing to compare in Try models. | Version 1 result, about **02:00** | Simplify the output: take the quote field out of the Mubit task and find quotes in plain code instead. Send more examples. | 🟠 | |
| M5 | Version comes back "Prompt only" (the base open model with our prompt did as well as an adapter). | No adapter appears, because the task is too easy. | Same as M4 | See C1: Northwind's own categories and house rules. | 🟠 | |
| M6 | Try models allows 3 adapter starts per day, the first start takes several minutes, and there's a daily cap on calls. | Expo judges arrive one by one over two hours. | Office hours Q5 | Start it once at 10:15 and keep the page open. Have recordings of the console beats. Use at most one start during rehearsal. | 🟠 | |
| M7 | A task is defined by its exact system prompt, tools, output format and model. Change one word and you get a new task with zero examples. | All our examples split across tasks and nothing trains. | Code review | Keep the system prompt as a constant in one file, frozen after 21:30. Customer text, channel and corrections all go in the user message. | 🟢 rule set | |
| M8 | Mubit records prompts and replies by default. | Real customer data would leak. | — | Use synthetic data only. Never paste a real message. | 🟢 | |
| M9 | Mubit answers no browser (CORS) requests. | Calls straight from the frontend fail. | — | Every Mubit call goes through our backend. | 🟢 | |
| M10 | The starter credit only covers some models and paths, and there's no audio path. | Speech-to-text through Mubit needs our own OpenAI key. | Office hours Q8 | Use a separate speech-to-text service (see V2). | 🟠 | |
| M11 | Unknown whether the adapter can be exported or hosted by the firm. | The "own your model, keep health data in-house" argument depends on it. | Office hours Q7 | If not, drop that argument and lead on cost, versions and audit. | 🟠 | |
| M12 | Adapter running cost is unknown. | The money screen needs a cost per million messages. | Office hours Q6 | Show measured latency plus token counts, and say "cost from Mubit's pricing". Never invent a number. | 🟠 | |
| M13 | There may be no API for task or adapter status. | Our app can't show "training now" live. | Office hours Q3 | The model panel shows our own counts (corrections, examples sent). Use the console tab for the rest. | 🟠 | |
| M14 | **Duplicate calls don't count as kept examples.** On Redline, 150 calls sat at 23 kept for hours. | The adapter never reaches 25 kept examples. | Learned on Redline | At least 40 **varied** synthetic cases per task, sent early with the final prompt and playbook. The warm-up script only sends combinations it hasn't sent before. | 🟢 rule set | |
| M15 | **Same prompt on two models makes two tasks.** | Examples split across two tasks and neither trains. | Learned on Redline | One model per task, fixed in `.env`. | 🟢 rule set | |
| M16 | `metadata.session_id` only works if OpenAI's `store=true` is on, and we don't want OpenAI storing calls. | My earlier idea of reusing the session ID as the case ID doesn't work. | Learned on Redline | Don't send it. Use our own case IDs in our database. | 🟢 | |
| M17 | A Bad rating doesn't remove a call from training. Only `x-middleware-record: metadata` does. | Held-out and base runs would leak into training. | Mubit team | Base and held-out runs use `metadata` **set in code**, not remembered (Redline leaked a held-out pack this way once). | 🟢 rule set | |
| M18 | **Latency through Mubit (JSON):** gpt-6-luna takes about 3–4s per call, gpt-4o-mini and gpt-4.1-mini about 1.4s. | Voice turns feel slow, and the live flags lag. | Measured on Redline | Use a small model for voice turns and stream them. Run triage in the background during the call. | 🟠 | |
| M19 | **Redress has 5 Mubit tasks** (voice turn, triage, decide, letter, induce rule). Each needs 25+ varied kept examples to train. | Training spreads thin, and nothing passes by the morning. | Planning | Choose **one hero task for the adapter story**, probably `complaint.triage` (or `decide`), and warm that one first. The other tasks still go through Mubit, but they're not the one we show training. | 🔴 decide now | |

## B. Risks specific to Catch

| # | Risk | Fix | Status | Owner |
|---|---|---|---|---|
| C1 | **The task may be too easy.** Big models already know the FCA definition, so there's no before/after. | Invent **Northwind Finance**, with 8 complaint categories of its own and 3 house rules no model knows. **Check by 21:30:** run 50 hard messages through the big model with no examples. It needs to get at least 15% wrong, or we make the task harder. | 🔴 | |
| C2 | **We'd be marking our own homework.** We write, label, correct and test the data ourselves. | A written labelling rubric quoting the FCA definition and FG21/1's four vulnerability drivers. A test set of 200, frozen before any corrections. The recruited expert checks 20 labels. | 🟠 | |
| C3 | **The money screen overstates.** Not every missed complaint reaches the ombudsman, and the first 3 cases a year are free. | Present £650 as risk ("each one that reaches the ombudsman"). The hard number is the measured cost per million messages, plus the share of messages checked (100% instead of a 5–10% sample). | 🟠 | |
| C4 | **Aveni, NICE and Voyc already do this.** Correction at 21:25: Aveni's File Check page says overrides "feed the next assessment release", so they *do* learn from overrides. | Treat them as proof lenders pay for it. Wedge: "their overrides feed the next release of *their* model; ours change the next call straight away and the bank's *own* model overnight." Never say they don't learn. | 🟠 | |
| C5 | **No finance person on the team.** | Read CATCH_BRIEF.md (15 min). Recruit someone who has worked in complaints, contact-centre QA or compliance by **21:30** and get one quotable sentence. | 🔴 | |
| C6 | **Claims we haven't verified yet:** the exact rule VW broke under DISP (we've only seen secondary sources); whether Aveni trains per client; Aveni's "25× cheaper" and "5–10% sampling" (their own marketing); any cost number we haven't measured. | Only quote these as "Aveni says…", or after checking the primary source. | 🟠 | |
| C7 | A judge says "isn't this just prompt examples plus distillation?" | Answer honestly: "Yes, and that's the point. Fixes work in seconds through the prompt, then become a cheaper, versioned, tested model through Mubit." Lead on whatever M1 turns out to allow. | 🟠 | |

## C. Voice risks

| # | Risk | Fix | Status | Owner |
|---|---|---|---|---|
| V1 | **A second risky integration.** Live voice on top of Mubit. | One owner. **Hard cap 01:00:** if live transcription isn't working by then, play a pre-recorded call through the same pipeline. It's still real speech-to-text and real Mubit calls, just not a live speaker. | 🟠 | |
| V2 | **The speech-to-text route.** Mubit's starter credit has no audio path, and the rules may count speech-to-text. | Ask the organisers. Default: the browser's built-in speech recognition (Chrome) or Deepgram for speech-to-text, and every LLM call through Mubit. | 🟠 | |
| V3 | **Venue noise.** | Push-to-talk on a phone held close, or a headset. Rehearse once in the actual room. | 🟠 | |
| V4 | **Delay between speaking and the flag appearing.** | Classify once per customer turn, using the last 6 turns, streaming. Target under 3 seconds from end of speech to flag. Measure it. | 🟠 | |
| V5 | **A real phone number** (Twilio UK numbers need address checks). | Don't, for the main demo. Use a browser "Call Northwind" page on a phone. A real number is a stretch goal only, after 06:00. | 🟢 decided | |
| V6 | **Venue wifi drops.** | Phone hotspot, tested with the laptop actually connected. Every live call falls back to a saved fixture. | 🟠 | |

## D. Demo and logistics

| # | Risk | Fix | Status |
|---|---|---|---|
| D1 | Demo length unknown | Ask Max. Prepare a 3:00 and a 2:00 cut. | 🔴 |
| D2 | Expo (judges at the table) and stage need different versions | A 30-second loop that runs on its own, plus a guided version | 🟠 |
| D3 | Mubit console logs out or is slow on stage | Stay logged in. Screen-record every console beat at 08:00. | 🟠 |
| D4 | Too much scope (voice + Aveni features + learning loop) in about 14 hours | Cut order below. Feature freeze at **08:00** with no exceptions. | 🟠 |
| D5 | Rules: new code only; public repo registered with Max; **every** LLM call through Mubit (the amplifier, the eval checks, agent nudges, any voice-agent brain); at least one of us at Sunday's demos | Check the repo at 21:00 and again at the freeze | 🟠 |
| D6 | Clocks go back at 02:00 | Phone alarms follow the phone clock automatically. Write every deadline in BST and double-check after 02:00. | 🟢 |
| D7 | Nobody sleeps, and the demo suffers | Take turns: two people sleep 03:00–06:00, the other two 05:00–08:00 | 🟠 |

## E. Judge questions we can't answer yet

- "Prove the model update came from the correction." Depends on M1.
- "What does it cost per million messages?" Depends on M12 and our measurement.
- "How does it do on real messages?" Depends on C2 and the expert's check.
- "Who buys this and for how much?" Default answer: the head of complaints or QA. Aveni has 250+ firm customers and raised £12m with Lloyds and Nationwide investing. Don't quote a price.

## Cut order (first thing to drop at the top)

1. A real phone number (V5)
2. The version 3 "rules changed" retrain (show the instant layer only)
3. The emerging-trend tile
4. The case view joining a call and an email
5. Drafted acknowledgement letter (fall back to a fixed template)
6. **Never cut:** a live call or message being flagged with its quote · a reviewer override with a reason · the version history and side-by-side comparison in Mubit · the money screen
