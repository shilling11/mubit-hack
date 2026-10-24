"""Deepgram pre-recorded transcription (not an LLM call, so it doesn't go through Mubit).

Demo setup B: one mixed track (a phone on speaker next to the laptop), so we use
Deepgram's diarisation to separate the two speakers.
"""
import httpx

from app.config import DEEPGRAM_API_KEY, DEEPGRAM_MODEL

URL = "https://api.deepgram.com/v1/listen"
PARAMS = {
    "model": DEEPGRAM_MODEL,
    "language": "en",
    "diarize": "true",
    "utterances": "true",
    "smart_format": "true",
    "punctuate": "true",
}


class STTError(RuntimeError):
    pass


def _parse(body: dict) -> dict:
    results = body.get("results", {})
    utts = [
        {"speaker": int(u.get("speaker", 0)), "text": u.get("transcript", "").strip(),
         "start_s": float(u.get("start", 0)), "end_s": float(u.get("end", 0)),
         "confidence": float(u.get("confidence", 0))}
        for u in results.get("utterances", []) if u.get("transcript", "").strip()
    ]
    alt = (results.get("channels") or [{}])[0].get("alternatives") or [{}]
    return {
        "utterances": utts,
        "confidence": float(alt[0].get("confidence", 0)) if alt else 0.0,
        "duration_s": float(body.get("metadata", {}).get("duration", 0)),
    }


def transcribe(audio: bytes, mimetype: str) -> dict:
    """Returns {utterances:[{speaker:int, text, start_s, end_s, confidence}], confidence, duration_s}."""
    if not DEEPGRAM_API_KEY:
        raise STTError("DEEPGRAM_API_KEY is not set")
    r = httpx.post(URL, params=PARAMS, content=audio, timeout=120,
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
