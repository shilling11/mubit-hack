# Calling: record a real call, transcribe it, review it (for Sultan)

**What to build:**
- a **Record call** button in the web app that records the laptop mic;
- on Stop, upload the audio to `POST /api/calls`;
- the backend sends it to **Deepgram (pre-recorded, with speaker separation)**, saves the utterances labelled agent or customer, and runs `review.<client>` through Mubit.

Target: a 90-second call has a scorecard **within 20 seconds of hanging up**.

**Not needed in v3:** a live voice agent, live nudges, text-to-speech, a WebRTC call room or ngrok. The call is just a **recording reviewed after it ends**, which is how QA works in real life (see QA_RESEARCH.md §3).

> If your LiveKit two-track setup from the listen-in design already works, keep it: separate tracks give exact speaker labels. Otherwise use the single-mic path below and let Deepgram separate the speakers.

---

## 1. Setup on the day (Option A, the default)

- **Sultan** plays the customer **Ellen Hart** and rings **Abdul's phone**. It's an ordinary phone call, so no telephony integration is needed.
- **Abdul** plays the Thistle Bank agent **Sam**, with the phone **on speaker, next to the laptop**.
- **The laptop** runs the web app on the projector and records through its microphone.

**Option B:** both stand near the laptop and role-play in person. The audio is cleaner but it looks less real.

**Fallback:** a pre-recorded file of the same script (record it tonight). The app has an **Upload file** button next to Record.

---

## 2. Frontend (recorder)

```js
// web: Record / Stop. Chrome records audio/webm;codecs=opus by default
const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: false, noiseSuppression: true } });
const rec = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
const chunks = []; rec.ondataavailable = e => chunks.push(e.data);
rec.onstop = async () => {
  const fd = new FormData();
  fd.append("audio", new Blob(chunks, { type: "audio/webm" }), "call.webm");
  fd.append("client_id", "thistle"); fd.append("agent_name", "Sam");
  const { call_id } = await (await fetch(`${API}/api/calls`, { method: "POST", body: fd })).json();
  // then poll GET /api/calls/{call_id} until review is present, and open the evaluation form
};
```
- The mic needs `localhost` or HTTPS. Running the web app on the same laptop at `http://localhost:3000` is fine.
- Show a recording timer and a level meter, so people can see it's working on stage.

---

## 3. Backend: `POST /api/calls`

1. Save the upload to `data/audio/{call_id}.webm`.
2. **Deepgram pre-recorded:**
   ```text
   POST https://api.deepgram.com/v1/listen?model=nova-3&diarize=true&utterances=true&smart_format=true&punctuate=true&language=en
   Authorization: Token $DEEPGRAM_API_KEY
   Content-Type: audio/webm
   <bytes>
   ```
   Read `results.utterances[]`, each with `{ start, end, transcript, speaker, confidence }`.
   `TODO(verify)`: the current model name (nova-3 or newer), `en-GB` support, and whether `redact=pci` is still available.
3. **Work out who's the agent:**
   - The speaker whose first utterance contains the bank greeting ("Thistle Bank", "how can I help") is `agent`, and the other is `customer`.
   - Otherwise, whoever speaks first is the agent.
   - Add a **Swap speakers** button in the UI, just in case.
4. **Redact before any model call** (regex): card numbers (13–19 digits), sort codes (`\d{2}-\d{2}-\d{2}`), account numbers (8 digits), dates of birth, postcodes. Replace with `[CARD]`, `[SORT]` and so on.
5. Save `utterances` (speaker, text, start_s, end_s), then run **`review.thistle`** through `app/llm/mubit_client.py`. The user message is the transcript with timestamps plus the current playbook rules.
6. Route the call into the right queue (ARCHITECTURE §3) and return `{ call_id }`.

**Speech-to-text is not an LLM call**, so it goes to Deepgram directly. Every model call goes through Mubit. Ask Max on Discord to confirm speech-to-text is fine outside Mubit.

**Batch import** (for the 100 synthetic calls): `POST /api/calls/import` with `{ client_id, calls:[{ agent_name, utterances:[{ speaker, text, start_s, end_s }] }] }`. No audio, same review path.

---

## 4. The scripted demo call (about 90 seconds)

Sam handles it **badly on purpose**, so the scorecard has real failures to catch.

| # | Speaker | Line | What the review should catch |
|---|---|---|---|
| 1 | Sam | "Thistle Bank, Sam speaking, how can I help?" | — |
| 2 | Ellen | "Hi, I've been charged overdraft fees three times this month and I'm really not happy about it." | **A complaint** (unhappy + lost money) |
| 3 | Sam | "Can I take your name and date of birth, and the first line of your address?" | C4 identity check: **pass** |
| 4 | Ellen | "Ellen Hart, [DOB], 12 Hill Street." | Redacted |
| 5 | Sam | "Thanks Ellen. Yes, I can see three £25 fees." | — |
| 6 | Ellen | "I was in hospital for two weeks and couldn't sort my account out." | **Vulnerability: health** |
| 7 | Sam | "Oh right. Don't worry, I'm sure we'll refund all of that for you." | **C3 fail: promised an outcome** |
| 8 | Ellen | "When will I know?" | — |
| 9 | Sam | "Someone will be in touch. Anything else?" | **S1 fail:** no deadline or next steps · **C1 fail:** never says it's logged as a complaint · **C2 fail:** no support offered |
| 10 | Ellen | "No, that's it." | — |

Expected result: **FAIL, with 3 critical fails** (C1, C2, C3) and S1 marked down, each with the quote and its timestamp.

**Rehearse it 3 times.** Record the best take as the fallback file.

---

## 5. Done when

- [ ] Record → Stop → scorecard visible in **≤ 20 s** for the 90-second script (measure it)
- [ ] Speakers labelled correctly in 3 out of 3 rehearsal takes (or fixed in one click with Swap)
- [ ] Every failed item's quote has a timestamp that plays the audio from that point
- [ ] The card number and date of birth are redacted in what's sent to Mubit (check the Mubit Requests page)
- [ ] The fallback file uploads and gives the same result
- [ ] The 100 synthetic calls import and review without errors (the review tests run with `record=metadata` on the held-out 25)

## 6. Keys (`.env`, never in chat or git)
```bash
MUBIT_BASE_URL=https://api.mubit.ai/openai/v1
MUBIT_API_KEY=mbt_...
MUBIT_MODEL=gpt-6-luna            # one model for review.* and report.* (fixed)
DEEPGRAM_API_KEY=...
GMAIL_USER=harbour.assurance.demo@gmail.com   # sends client reports and escalations
GMAIL_APP_PASSWORD=...                        # needs 2-Step Verification on that account
```
