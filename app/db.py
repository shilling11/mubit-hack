"""SQLite store for traces, runs, drafts, corrections and playbook versions."""
import json
import sqlite3
import threading
from contextlib import contextmanager
from typing import Any, Iterator

from app.config import DB_PATH

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    task TEXT NOT NULL,
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
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    package TEXT NOT NULL,
    playbook_version INTEGER NOT NULL,
    model TEXT NOT NULL,
    label TEXT,
    status TEXT NOT NULL,
    created REAL NOT NULL,
    finished REAL,
    total INTEGER NOT NULL DEFAULT 0,
    done INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    score_json TEXT
);
CREATE TABLE IF NOT EXISTS drafts (
    run_id TEXT NOT NULL,
    req_id TEXT NOT NULL,
    sheet TEXT,
    category TEXT,
    requirement TEXT,
    mandatory TEXT,
    priority TEXT,
    status TEXT,
    response TEXT,
    evidence_ids TEXT,
    gaps TEXT,
    confidence REAL,
    flags TEXT,
    retrieved TEXT,
    request_id TEXT,
    served_by TEXT,
    latency_ms INTEGER,
    tokens_in INTEGER,
    tokens_out INTEGER,
    verify_json TEXT,
    error TEXT,
    PRIMARY KEY (run_id, req_id)
);
CREATE TABLE IF NOT EXISTS corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    package TEXT,
    run_id TEXT,
    req_id TEXT NOT NULL,
    requirement TEXT NOT NULL,
    model_output TEXT,
    corrected_output TEXT NOT NULL,
    correction_type TEXT,
    rationale TEXT NOT NULL,
    editor TEXT,
    request_id TEXT,
    rule TEXT
);
CREATE TABLE IF NOT EXISTS playbook_versions (
    version INTEGER PRIMARY KEY,
    created REAL NOT NULL,
    correction_ids TEXT NOT NULL,
    rules TEXT NOT NULL,
    note TEXT
);
"""

JSON_COLS = {
    "evidence_ids", "flags", "retrieved", "verify_json", "score_json",
    "model_output", "corrected_output", "correction_type", "correction_ids", "rules",
}


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


def init() -> None:
    with tx() as c:
        c.executescript(SCHEMA)


def _encode(v: Any) -> Any:
    return json.dumps(v) if isinstance(v, (dict, list)) else v


def _decode(row: sqlite3.Row) -> dict:
    out = dict(row)
    for k in JSON_COLS & out.keys():
        if out[k] is not None:
            out[k] = json.loads(out[k])
    return out


def insert(table: str, data: dict) -> int:
    cols = ", ".join(data)
    marks = ", ".join("?" for _ in data)
    with tx() as c:
        cur = c.execute(f"INSERT INTO {table} ({cols}) VALUES ({marks})", [_encode(v) for v in data.values()])
        return cur.lastrowid


def upsert(table: str, data: dict) -> None:
    cols = ", ".join(data)
    marks = ", ".join("?" for _ in data)
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
