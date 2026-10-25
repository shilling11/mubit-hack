"""Deepgram pre-recorded transcription (not an LLM call, so it doesn't go through Mubit).

Demo setup B: one mixed track (a phone on speaker next to the laptop), so we use
Deepgram's diarisation to separate the two speakers.
Demo setup A (phones): a two-channel recording, one speaker per channel, so we transcribe
each channel separately (multichannel) and the channel is the speaker.
"""
import httpx

from app.config import DEEPGRAM_API_KEY, DEEPGRAM_MODEL, DEEPGRAM_UTT_SPLIT

URL = "https://api.deepgram.com/v1/listen"
PARAMS = {
    "model": DEEPGRAM_MODEL,
    "language": "en",
    "diarize": "true",
    "utterances": "true",
    "utt_split": DEEPGRAM_UTT_SPLIT,
    "smart_format": "true",
    "punctuate": "true",
}
MULTICHANNEL_PARAMS = {**{k: v for k, v in PARAMS.items() if k != "diarize"}, "multichannel": "true"}


class STTError(RuntimeError):
    pass


def _parse(body: dict) -> dict:
    results = body.get("results", {})
    utts = [
        {"speaker": int(u.get("speaker", 0)), "channel": int(u.get("channel", 0)),
         "text": u.get("transcript", "").strip(),
         "start_s": float(u.get("start", 0)), "end_s": float(u.get("end", 0)),
         "confidence": float(u.get("confidence", 0)),
         # per-word timestamps: to silence redacted words in the stored audio, and to tell echo
         # (same words at the same moment on both channels) from replies
         "words": [{"word": w.get("word", ""), "punctuated_word": w.get("punctuated_word", ""),
                    "start": float(w.get("start", 0)), "end": float(w.get("end", 0))} for w in u.get("words", [])]}
        for u in results.get("utterances", []) if u.get("transcript", "").strip()
    ]
    alts = [(ch.get("alternatives") or [{}])[0] for ch in results.get("channels") or [{}]]
    return {
        "utterances": sorted(utts, key=lambda u: u["start_s"]),
        "confidence": sum(float(a.get("confidence", 0)) for a in alts) / len(alts),
        "duration_s": float(body.get("metadata", {}).get("duration", 0)),
    }


def transcribe(audio: bytes, mimetype: str, *, multichannel: bool = False) -> dict:
    """Returns {utterances:[{speaker:int, channel:int, text, start_s, end_s, confidence}], confidence, duration_s}."""
    if not DEEPGRAM_API_KEY:
        raise STTError("DEEPGRAM_API_KEY is not set")
    r = httpx.post(URL, params=MULTICHANNEL_PARAMS if multichannel else PARAMS, content=audio, timeout=120,
                   headers={"Authorization": f"Token {DEEPGRAM_API_KEY}", "Content-Type": mimetype or "audio/webm"})
    if r.status_code >= 400:
        raise STTError(f"Deepgram {r.status_code}: {r.text[:300]}")
    return _parse(r.json())


def transcribe_url(url: str) -> dict:
    """Transcribe audio Deepgram can fetch itself (used for the connectivity check)."""
    if not DEEPGRAM_API_KEY:
        raise STTError("DEEPGRAM_API_KEY is not set")
    r = httpx.post(URL, params=PARAMS, json={"url": url}, timeout=120,
                   headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"})
    if r.status_code >= 400:
        raise STTError(f"Deepgram {r.status_code}: {r.text[:300]}")
    return _parse(r.json())
