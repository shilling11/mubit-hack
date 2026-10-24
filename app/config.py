import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DATA = ROOT / "data"
AUDIO_DIR = DATA / "audio"          # raw call audio stays on this machine (gitignored)
CALLS_DIR = DATA / "calls"
DEMO_DIR = DATA / "demo"
EVAL_DIR = DATA / "eval"
CORRECTIONS_DIR = DATA / "corrections"
SCORECARD_PATH = DATA / "scorecard.json"
CUSTOMERS_PATH = DATA / "customers.json"
DB_PATH = Path(os.getenv("REDRESS_DB", ROOT / "redress.db"))

MUBIT_BASE_URL = os.getenv("MUBIT_BASE_URL", "https://api.mubit.ai/openai/v1")
MUBIT_API_KEY = os.getenv("MUBIT_API_KEY", "")
# One fixed model for review.call and rule.induce: Mubit forms a task from model + system prompt + output format.
MUBIT_MODEL = os.getenv("MUBIT_MODEL", "gpt-6-luna")
BASELINE_MODEL = os.getenv("BASELINE_MODEL", "gpt-6-sol")
# Measured on the demo calls: default ~18.6s per review, "low" ~13.5s, "none" ~10s. Keep it fixed once chosen.
REVIEW_REASONING_EFFORT = os.getenv("REVIEW_REASONING_EFFORT", "low") or None

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
DEEPGRAM_MODEL = os.getenv("DEEPGRAM_MODEL", "nova-3")

# Conservative routing (README §4.5). Tune on practice calls, never on held-out ones.
AUDIT_RATE = float(os.getenv("REDRESS_AUDIT_RATE", "0.05"))
CRITICAL_CONFIDENCE = float(os.getenv("REDRESS_CRITICAL_CONFIDENCE", "0.8"))
SCORED_CONFIDENCE = float(os.getenv("REDRESS_SCORED_CONFIDENCE", "0.6"))
STT_MIN_CONFIDENCE = float(os.getenv("REDRESS_STT_MIN_CONFIDENCE", "0.75"))

# Base (playbook v0) and held-out reviews are recorded without content, so they never train Mubit.
HELD_OUT_RECORD = os.getenv("REDRESS_HELD_OUT_RECORD", "metadata")
MAX_PARALLEL = int(os.getenv("REDRESS_MAX_PARALLEL", "4"))
