"""SQLite store for calls, reviews, routing, evaluations, corrections, playbooks and traces."""
import json
import sqlite3
import threading
from contextlib import contextmanager
from typing import Any, Iterator

from app.config import DB_PATH

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS calls (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,            -- live | upload | synthetic | demo
    split TEXT NOT NULL,             -- practice | heldout | live
    agent_name TEXT,
    audio_path TEXT,
    duration_s REAL,
    stt_confidence REAL,
    status TEXT NOT NULL DEFAULT 'new',  -- new | transcribing | reviewing | scored | failed
    error TEXT,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS utterances (
    call_id TEXT NOT NULL,
    idx INTEGER NOT NULL,
    speaker TEXT NOT NULL,           -- agent | customer
    text_raw TEXT NOT NULL,
    text_redacted TEXT NOT NULL,
    start_s REAL NOT NULL,
    end_s REAL,
    confidence REAL,
    PRIMARY KEY (call_id, idx)
);
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id TEXT NOT NULL,
    run_id TEXT,
    playbook_version INTEGER NOT NULL,
    model TEXT NOT NULL,
    record_mode TEXT NOT NULL,
    request_id TEXT,
    served_by TEXT,
    latency_ms INTEGER,
    tokens_in INTEGER,
    tokens_out INTEGER,
    output_json TEXT,                -- model output after the evidence check
    items_json TEXT,                 -- per-item final answers used for scoring
    score REAL,
    pass INTEGER,
    critical_fails TEXT,
    risk_tier TEXT,
    issues_json TEXT,                -- evidence-check issues
    error TEXT,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS queue (
    call_id TEXT PRIMARY KEY,
    review_id INTEGER,
    kind TEXT NOT NULL,              -- breach | analyst | audit | auto
    reasons_json TEXT,
    audit INTEGER NOT NULL DEFAULT 0,
    due_at REAL,
    done INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id TEXT NOT NULL,
    review_id INTEGER NOT NULL,
    analyst TEXT,
    items_json TEXT NOT NULL,
    comments TEXT,
    submitted_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id TEXT,
    review_id INTEGER,
    item_id TEXT NOT NULL,
    before TEXT,
    after TEXT NOT NULL,
    reason TEXT NOT NULL,
    excerpt TEXT,
    source TEXT NOT NULL DEFAULT 'analyst',  -- analyst | seed
    rule_json TEXT,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS playbook_versions (
    version INTEGER PRIMARY KEY,
    created_at REAL NOT NULL,
    correction_ids TEXT NOT NULL,
    rules_json TEXT NOT NULL,
    note TEXT
);
CREATE TABLE IF NOT EXISTS agreement (
    item_id TEXT PRIMARY KEY,
    n INTEGER NOT NULL DEFAULT 0,
    agreed INTEGER NOT NULL DEFAULT 0,
    updated_at REAL
);
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    label TEXT,
    split TEXT NOT NULL,
    playbook_version INTEGER NOT NULL,
    model TEXT NOT NULL,
    status TEXT NOT NULL,
    total INTEGER NOT NULL DEFAULT 0,
    done INTEGER NOT NULL DEFAULT 0,
    metrics_json TEXT,
    error TEXT,
    created_at REAL NOT NULL,
    finished_at REAL
);
CREATE TABLE IF NOT EXISTS traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    task TEXT NOT NULL,
    call_id TEXT,
    run_id TEXT,
    request_id TEXT,
    model_asked TEXT,
    served_by TEXT,
    record_mode TEXT,
    latency_ms INTEGER,
    tokens_in INTEGER,
    tokens_out INTEGER,
    ok INTEGER NOT NULL,
    error TEXT
);
CREATE INDEX IF NOT EXISTS reviews_call ON reviews (call_id, id);
"""

JSON_COLS = {"output_json", "items_json", "critical_fails", "issues_json", "reasons_json", "rule_json",
             "correction_ids", "rules_json", "metrics_json"}


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


@contextmanager
def tx() -> Iterator[sqlite3.Connection]:
    with _lock:
        conn = _connect()
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


MIGRATIONS = [
    "ALTER TABLE calls ADD COLUMN customer_name TEXT",  # names to redact for this call
    "ALTER TABLE calls ADD COLUMN audio_muted INTEGER",  # redacted words silenced in the audio (-1: not WAV)
]


def init() -> None:
    with tx() as c:
        c.executescript(SCHEMA)
        for m in MIGRATIONS:
            try:
                c.execute(m)
            except sqlite3.OperationalError:
                pass  # already applied


def _encode(v: Any) -> Any:
    return json.dumps(v) if isinstance(v, (dict, list)) else v


def _decode(row: sqlite3.Row) -> dict:
    out = dict(row)
    for k in JSON_COLS & out.keys():
        if out[k] is not None:
            out[k] = json.loads(out[k])
    return out


def insert(table: str, data: dict) -> int:
    cols, marks = ", ".join(data), ", ".join("?" for _ in data)
    with tx() as c:
        return c.execute(f"INSERT INTO {table} ({cols}) VALUES ({marks})", [_encode(v) for v in data.values()]).lastrowid


def upsert(table: str, data: dict) -> None:
    cols, marks = ", ".join(data), ", ".join("?" for _ in data)
    with tx() as c:
        c.execute(f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({marks})", [_encode(v) for v in data.values()])


def update(table: str, key: dict, data: dict) -> None:
    sets = ", ".join(f"{k} = ?" for k in data)
    where = " AND ".join(f"{k} = ?" for k in key)
    with tx() as c:
        c.execute(f"UPDATE {table} SET {sets} WHERE {where}", [_encode(v) for v in data.values()] + list(key.values()))


def query(sql: str, params: tuple = ()) -> list[dict]:
    with tx() as c:
        return [_decode(r) for r in c.execute(sql, params).fetchall()]


def one(sql: str, params: tuple = ()) -> dict | None:
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql: str, params: tuple = ()) -> None:
    with tx() as c:
        c.execute(sql, params)
