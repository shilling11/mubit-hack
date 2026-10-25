"""Silence redacted words in a stored WAV recording (README §4.3).

Deepgram returns a timestamp for every word. Words that fall inside a text
redaction (date of birth, card number, name, address...) are muted in the saved
file, so the recording the analyst plays back no longer contains them. Works on
uncompressed PCM WAV (what the Live call recorder produces); other formats are
left as they are and reported.
"""
import wave
from pathlib import Path

from app.privacy.redact import spans

PAD_S = 0.08  # mute a little either side of each word


def redacted_ranges(utterances: list[dict], extra_names: list[str] | None = None) -> list[tuple[float, float]]:
    """utterances from stt.transcribe (with words). Returns time ranges (seconds) to silence."""
    ranges: list[tuple[float, float]] = []
    for u in utterances:
        words = u.get("words") or []
        if not words:
            continue
        # Rebuild the line from its words so character offsets map back to words
        text, offsets = "", []
        for w in words:
            token = w.get("punctuated_word") or w.get("word") or ""
            start = len(text) + (1 if text else 0)
            text = f"{text} {token}" if text else token
            offsets.append((start, start + len(token), w))
        for s, e, _ in spans(text, extra_names):
            for a, b, w in offsets:
                if a < e and b > s:
                    ranges.append((max(0.0, float(w["start"]) - PAD_S), float(w["end"]) + PAD_S))
    # merge overlaps
    ranges.sort()
    merged: list[tuple[float, float]] = []
    for a, b in ranges:
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    return merged


def is_wav(path: str | Path) -> bool:
    with open(path, "rb") as f:
        head = f.read(12)
    return head[:4] == b"RIFF" and head[8:12] == b"WAVE"


def mute_wav(path: str | Path, ranges: list[tuple[float, float]]) -> int:
    """Overwrite the given time ranges with silence, in place. Returns the number of ranges muted."""
    if not ranges:
        return 0
    with wave.open(str(path), "rb") as r:
        params = r.getparams()
        frames = bytearray(r.readframes(r.getnframes()))
    if params.comptype != "NONE":
        return 0
    frame_bytes = params.sampwidth * params.nchannels
    silence = b"\x80" if params.sampwidth == 1 else b"\x00"  # 8-bit WAV is unsigned
    n = 0
    for a, b in ranges:
        i = max(0, int(a * params.framerate)) * frame_bytes
        j = min(len(frames), int(b * params.framerate) * frame_bytes)
        if j > i:
            frames[i:j] = silence * (j - i)
            n += 1
    with wave.open(str(path), "wb") as w:
        w.setparams(params)
        w.writeframes(bytes(frames))
    return n
