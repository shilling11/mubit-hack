import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DATA = ROOT / "data"
RFPS = DATA / "rfps"
KB_DIR = DATA / "company_kb"
EVAL_DIR = DATA / "eval"
CORRECTIONS_DIR = DATA / "corrections"
EXPORTS = ROOT / "exports"
DB_PATH = Path(os.getenv("REDLINE_DB", ROOT / "redline.db"))

MUBIT_BASE_URL = os.getenv("MUBIT_BASE_URL", "https://api.mubit.ai/openai/v1")
MUBIT_API_KEY = os.getenv("MUBIT_API_KEY", "")
# Model the bid tasks run on. Mubit trains task adapters from these calls.
MUBIT_MODEL = os.getenv("MUBIT_MODEL", "gpt-6-luna")
# Larger closed model for the Track 2 quality/cost/latency comparison.
BASELINE_MODEL = os.getenv("BASELINE_MODEL", "gpt-6-sol")

MAX_PARALLEL = int(os.getenv("REDLINE_MAX_PARALLEL", "4"))
KB_TOP_K = int(os.getenv("REDLINE_KB_TOP_K", "4"))

COMPANY_NAME = "Ashgrove Digital"
