"""Load the two demo call scripts as calls (text versions, used for rehearsal and as a fallback)."""
import json

from app.capture import ingest
from app.config import DEMO_DIR


def scripts() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(DEMO_DIR.glob("call*.json"))]


def load_script(script_id: str) -> str:
    s = next(x for x in scripts() if x["id"] == script_id)
    utts = s["utterances"]
    for i, u in enumerate(utts):
        u.setdefault("end_s", utts[i + 1]["start_s"] if i + 1 < len(utts) else u["start_s"] + 3)
    return ingest.create_call(utts, source="demo", split="live", agent_name=s["agent_name"], call_id=s["id"])
