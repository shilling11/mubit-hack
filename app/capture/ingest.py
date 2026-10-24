"""Turn a recording or an imported transcript into a stored call (raw + redacted utterances)."""
import re
import time
import uuid

from app import db
from app.config import AUDIO_DIR
from app.capture import stt
from app.privacy.redact import redact

AGENT_CUES = re.compile(r"thistle bank|how can i help|speaking|calling thistle|thanks for calling", re.I)
EXT = {"audio/webm": "webm", "audio/ogg": "ogg", "audio/wav": "wav", "audio/x-wav": "wav", "audio/mpeg": "mp3",
       "audio/mp4": "m4a", "audio/x-m4a": "m4a"}


def new_call_id(prefix: str = "call") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def agent_speaker(utts: list[dict]) -> int:
    """The speaker whose early lines contain a bank greeting is the colleague; otherwise whoever speaks first."""
    for u in utts[:4]:
        if AGENT_CUES.search(u["text"]):
            return u["speaker"]
    return utts[0]["speaker"] if utts else 0


def store_utterances(call_id: str, utterances: list[dict]) -> None:
    """utterances: [{speaker:"agent"|"customer", text, start_s, end_s?, confidence?}]"""
    db.execute("DELETE FROM utterances WHERE call_id = ?", (call_id,))
    for i, u in enumerate(utterances):
        db.insert("utterances", {
            "call_id": call_id, "idx": i, "speaker": u["speaker"], "text_raw": u["text"],
            "text_redacted": redact(u["text"]), "start_s": float(u.get("start_s", 0)),
            "end_s": u.get("end_s"), "confidence": u.get("confidence"),
        })


def create_call(utterances: list[dict], *, source: str, split: str, agent_name: str = "",
                call_id: str | None = None, duration_s: float | None = None,
                stt_confidence: float | None = None, audio_path: str | None = None) -> str:
    call_id = call_id or new_call_id()
    db.upsert("calls", {
        "id": call_id, "source": source, "split": split, "agent_name": agent_name, "audio_path": audio_path,
        "duration_s": duration_s if duration_s is not None else (utterances[-1].get("end_s") or utterances[-1]["start_s"]),
        "stt_confidence": stt_confidence, "status": "reviewing", "error": None, "created_at": time.time(),
    })
    store_utterances(call_id, utterances)
    return call_id


def save_recording(audio: bytes, mimetype: str, agent_name: str = "") -> str:
    """Save the upload and create the call record; transcription runs separately (it takes a few seconds)."""
    call_id = new_call_id("live")
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    path = AUDIO_DIR / f"{call_id}.{EXT.get((mimetype or '').split(';')[0], 'webm')}"
    path.write_bytes(audio)
    db.upsert("calls", {"id": call_id, "source": "live", "split": "live", "agent_name": agent_name,
                        "audio_path": str(path), "status": "transcribing", "created_at": time.time()})
    return call_id


def transcribe_call(call_id: str, mimetype: str) -> None:
    call = db.one("SELECT * FROM calls WHERE id = ?", (call_id,))
    audio = open(call["audio_path"], "rb").read()
    result = stt.transcribe(audio, mimetype)
    if not result["utterances"]:
        raise stt.STTError("no speech found in the recording")
    agent = agent_speaker(result["utterances"])
    utts = [{**u, "speaker": "agent" if u["speaker"] == agent else "customer"} for u in result["utterances"]]
    store_utterances(call_id, utts)
    db.update("calls", {"id": call_id}, {"duration_s": result["duration_s"], "stt_confidence": result["confidence"],
                                         "status": "reviewing"})


def swap_speakers(call_id: str) -> None:
    db.execute(
        "UPDATE utterances SET speaker = CASE speaker WHEN 'agent' THEN 'customer' ELSE 'agent' END WHERE call_id = ?",
        (call_id,),
    )
