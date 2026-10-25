# Redress demo runbook

Everything needed to set up, rehearse and run the demo: keys, links, files, the 3-minute run, timings we measured, and what to do when something breaks.

**The story in one line:** a real phone call is scored seconds after hang-up; it's one of Thistle's 81 calls this month; the analyst corrects one false alarm in one line, and Redress re-marks the whole month with it.

---

## 1. One-time setup

| What | Where | Notes |
|---|---|---|
| Mubit key | `.env` (project root) `MUBIT_API_KEY=mbt_…` | Never in `.env.example`, which is committed |
| Deepgram key | `.env` `DEEPGRAM_API_KEY=…` | Speech-to-text |
| Batch speed | `.env` `REDRESS_MAX_PARALLEL=8` | Scores 8 calls at a time (default 4) |
| LiveKit keys | `web/.env.local` `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` | The phone call. Also set in the Vercel project |

Start the two servers (two terminals, from the project root). **Restart the API after any `.env` change.**

```bash
.venv/Scripts/python -m uvicorn app.main:app --port 8000
```
```bash
npm --prefix web run dev
```

If you change the phone pages, redeploy them: `cd web` then `vercel deploy --prod`.

## 2. Links

| Who | Link |
|---|---|
| Laptop (projector): Home | http://localhost:3000 |
| Laptop: Live call | http://localhost:3000/dashboard/live |
| Laptop: Batch | http://localhost:3000/dashboard/batch |
| Laptop: the false-alarm call | http://localhost:3000/dashboard/calls/p044 |
| Sultan's phone (Ellen, the customer) | https://redress-three.vercel.app/call/customer |
| Abdul's phone (Sam, the colleague) | https://redress-three.vercel.app/call/agent |

The laptop must use **localhost**, not the Vercel site: only the laptop can open the line and record.

## 3. Files

| File | What it is |
|---|---|
| `data/batches/thistle-october-2026.xlsx` (and `.csv`) | Thistle's October export: 80 calls, one row per line (Call ID, Date, Agent, Speaker, Start, Text). Already imported |
| `scripts/make_batch.py` | Rebuilds that file from the practice calls (never the held-out ones or their labels): `.venv/Scripts/python -m scripts.make_batch` |
| `app/capture/importers.py` | Reads Excel/CSV, Amazon Connect (Contact Lens) JSON, pasted "Agent: … / Customer: …" text |
| `app/capture/tidy.py` | Transcript clean-up: drops echo, merges fragments, dates as "19 Dec 2004" |

## 4. Before every rehearsal (and before going on stage)

1. Reset: clears live calls, analyst checks, corrections and learned rules (back to playbook v0).
   ```bash
   curl -X POST http://localhost:8000/api/demo/reset
   ```
2. On **Batch**, press **Score the other 80 with playbook v0** if the "On playbook v0" count isn't 80/80. About 2 minutes.
3. Check the starting numbers: **playbook v0 · 80 calls · about 55 escalate now · about 10 to an analyst · about 15 auto-accepted**. p044 is one of the escalated calls.
4. Phones: open the two links above, allow the microphone, close any old tabs of the same link (a second tab takes the call over).
5. Once before the event: run the held-out evaluation on **Proof**, so the numbers on Home fill in.

## 5. The 3-minute run

| Time | Page | Do | Say (gist) |
|---|---|---|---|
| 0:00 | Home, top | — | "Ellen Hart spent two weeks in hospital… Banks hear one call in twenty." |
| 0:20 | Home, how it works | Scroll the steps | One line per step. "It'll make sense in a minute." |
| 0:40 | **Live call** | Colleague "Sam", Customer "Ellen Hart" → **Open the line** → Sultan taps **Call Thistle Bank** → Abdul taps **Answer** → the 30-second script → **End call** | — |
| ~1:15 | Live call | Scorecard appears: **FAIL · C1, C2, C3** | Hold 3 seconds. Say nothing |
| 1:20 | **Evaluation form** (Open the evaluation form →) | Click ▶ on the C2 quote: Sultan's voice, "I was in hospital for two weeks" → **Submit** with no changes | "Every finding points to the second she said it." The AI is right here, so Priya just confirms |
| 1:40 | **Batch** (See it in this month's batch →) | Ellen's call is first in "check these first", tagged *just taken* | "That call is one of 81 Thistle sent this month. Redress escalated 55." |
| 1:50 | **p044** (open its tile, or the link above) | AI failed C3 because Sam said "any fee the bank charges can never be refunded". Change **C3 → pass**, reason: **"Saying a fee can't be refunded is information, not a promised outcome."** → Submit | "Priya disagrees, in one line. That's now a rule." |
| 2:10 | **Batch** | **Score the other 79 with playbook v1** | "Priya taught it once. It's re-marking the whole month." Watch **Escalate now** drop |
| 2:30 | Mubit | Every call through Mubit | "Every correction is training data for Thistle's own model." |
| 2:45 | Home, bottom | Money and close | Calls checked: one in twenty → all of them. Closing line |

**What "Let Redress finish" means (step 3 on Batch):** after the analyst corrects a few calls, Redress re-marks every other call in the month with those corrections. The four boxes show the result: what still needs a person (escalate now, to an analyst, audit sample) and what it can sign off itself (auto-accepted).

## 6. Timings we measured (real Mubit and Deepgram)

| Step | Time |
|---|---|
| Hang-up → transcript on screen | about 3–5 s (Deepgram itself 1.5–3 s for an 86 s call) |
| Hang-up → scorecard | about 15–20 s (one Mubit review is about 14 s) |
| Correction → rule written | about 9 s |
| "Let Redress finish" → Escalate now starts dropping | the calls like the corrected one are re-marked first, so within about 15–20 s |
| "Let Redress finish" → whole month re-marked | about 2 minutes at 8 at a time |
| Scoring the 80-call batch from scratch | about 2.5 minutes at 8 at a time (about 5 at 4) |

Real rehearsal of the p044 correction (before the "re-mark similar calls first" fix): Escalate now went **56 → 50**, and the false alarm cleared on **4 of 7** similar calls. The model isn't deterministic, so expect roughly that, not exact numbers. Don't promise a number on stage.

## 7. If something breaks on stage

| Problem | Do this |
|---|---|
| A phone won't connect, or "Cancelled publication…" | The page now says why: usually the same link open twice. Close the other tab and call again |
| Call drops mid-way | Laptop: **Hang up & score** still scores what was recorded |
| No signal / the call won't work at all | Live call page: **Record call** (a phone on speaker next to the laptop) or **Upload file** |
| Audio fails completely | Live call page: **Demo call 1 (text)**. It joins the batch the same way |
| Scoring fails | The page says why (for example "MUBIT_API_KEY is not set"). Check `.env` and restart the API |

## 8. Pages: in the pitch or not

| Page | Use |
|---|---|
| Home, Live call, evaluation form, Batch | The pitch |
| Mubit | 10 seconds: "every call through Mubit" |
| Overview | Same information as Batch. Skip |
| Learning | Rules and corrections. Skip (Batch shows "rules learned") |
| Proof | Q&A: "how do you know it's accurate?" |

## 9. Known limits

- The untrained reviewer (v0) is strict: it escalates about 55 of 80. That's the point of the calibration step, but say "escalated", not "breaches found".
- Anyone with a phone link can ring the line while the laptop has it open. Handy at the expo (judges can call), but close the line otherwise.
- Not yet tested on real iPhones: whether call audio plays through the earpiece or the loudspeaker. If a phone shows "Tap to hear the call", tap it.
- Amazon Connect JSON import works, but there's no Amazon-format demo file yet; the October batch is Excel.
- The Vercel site is deployed from the laptop (`vercel deploy --prod` in `web/`); it isn't linked to GitHub.
