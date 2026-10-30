"""
SQLite storage for the portal: users, patients, vitals, triage, escalations,
referrals, surveillance signals, chat and the hash-chained audit log.
"""

import hashlib
import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime

from app.portal import config

_write_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS villages (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    block TEXT,
    district TEXT,
    state TEXT,
    lat REAL,
    lon REAL,
    created_by TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (name, district)
);

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    role TEXT NOT NULL,                 -- PATIENT | HEALTH_WORKER | DOCTOR | HEALTH_OFFICER
    name_enc TEXT NOT NULL,
    mobile_enc TEXT NOT NULL,
    mobile_hash TEXT NOT NULL,
    password_hash TEXT,
    status TEXT NOT NULL,               -- ACTIVE | PENDING_ACTIVATION | ERASED
    activation_hash TEXT,
    activation_expires TEXT,
    village_id TEXT,
    facility TEXT,
    created_by TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (role, mobile_hash)
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS patients (
    user_id TEXT PRIMARY KEY,
    pseudonym TEXT NOT NULL UNIQUE,
    age INTEGER,
    gender TEXT,
    village_id TEXT,
    conditions TEXT NOT NULL DEFAULT '[]',
    consent TEXT NOT NULL DEFAULT '{}',
    language TEXT DEFAULT 'hi',
    asha_id TEXT,
    next_visit TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vitals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    systolic INTEGER,
    diastolic INTEGER,
    glucose REAL,
    glucose_context TEXT,
    pulse INTEGER,
    spo2 INTEGER,
    weight_kg REAL,
    temperature_f REAL,
    source TEXT,
    recorded_by TEXT
);
CREATE INDEX IF NOT EXISTS idx_vitals_patient ON vitals (patient_id, recorded_at);

CREATE TABLE IF NOT EXISTS doses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    date TEXT NOT NULL,
    status TEXT NOT NULL,               -- TAKEN | MISSED
    reason TEXT,
    recorded_by TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (patient_id, date)
);

CREATE TABLE IF NOT EXISTS encounters (
    id TEXT PRIMARY KEY,
    patient_id TEXT,
    pseudonym TEXT NOT NULL,
    age INTEGER,
    gender TEXT,
    village_id TEXT,
    worker_id TEXT,
    language TEXT,
    vitals TEXT,
    transcripts TEXT NOT NULL DEFAULT '[]',
    symptoms TEXT NOT NULL DEFAULT '[]',
    danger_signs TEXT NOT NULL DEFAULT '[]',
    triage_level TEXT,
    rationale TEXT,
    checklist TEXT,
    citations TEXT,
    red_flag INTEGER DEFAULT 0,
    uncertain TEXT,
    summary_md TEXT,
    is_final INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    finalised_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_encounters_village ON encounters (village_id, created_at);

CREATE TABLE IF NOT EXISTS escalations (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,               -- TRIAGE | CHRONIC | CHAT
    level TEXT NOT NULL,
    status TEXT NOT NULL,               -- PENDING | REVIEWED
    patient_id TEXT,
    pseudonym TEXT,
    village_id TEXT,
    title TEXT,
    rationale TEXT,
    details TEXT NOT NULL DEFAULT '{}',
    review TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    doctor_id TEXT NOT NULL,
    title TEXT NOT NULL,
    category TEXT,
    status TEXT,
    summary TEXT,
    created_at TEXT NOT NULL,
    read_at TEXT
);

CREATE TABLE IF NOT EXISTS referrals (
    id TEXT PRIMARY KEY,
    patient_id TEXT,
    pseudonym TEXT NOT NULL,
    worker_id TEXT NOT NULL,
    village_id TEXT,
    encounter_id TEXT,
    hospital TEXT NOT NULL,
    reason TEXT,
    urgency TEXT,
    status TEXT NOT NULL,               -- REFERRED | REACHED | CANCELLED
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    village_id TEXT NOT NULL,
    date TEXT NOT NULL,
    pharmacy_ors_sales INTEGER,
    pharmacy_fever_sales INTEGER,
    school_absent INTEGER,
    school_enrolled INTEGER,
    reported_by TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (village_id, date)
);

CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    syndrome TEXT NOT NULL,
    village_ids TEXT NOT NULL,
    details TEXT NOT NULL,
    status TEXT NOT NULL,               -- ACTIVE | ACKNOWLEDGED
    ack_by TEXT,
    ack_note TEXT,
    ack_at TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    role TEXT NOT NULL,                 -- user | assistant
    content TEXT NOT NULL,
    language TEXT,
    flagged INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chat_patient ON chat_messages (patient_id, id);

CREATE TABLE IF NOT EXISTS audit_log (
    seq INTEGER PRIMARY KEY,
    ts TEXT NOT NULL,
    actor TEXT NOT NULL,
    role TEXT NOT NULL,
    event TEXT NOT NULL,
    details TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    hash TEXT NOT NULL
);
"""


def now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def today():
    return datetime.now().strftime('%Y-%m-%d')


@contextmanager
def connect():
    conn = sqlite3.connect(config.DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def transaction():
    """Serialised write transaction for multi-statement updates."""
    with _write_lock, connect() as conn:
        yield conn


def init():
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    with connect() as conn:
        conn.execute('PRAGMA journal_mode = WAL')
        conn.executescript(SCHEMA)


def query(sql, params=()):
    with connect() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def query_one(sql, params=()):
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql, params=()):
    with _write_lock, connect() as conn:
        cur = conn.execute(sql, params)
        return cur.lastrowid


def dumps(value):
    return json.dumps(value, ensure_ascii=False, default=str)


def loads(value, default=None):
    if value in (None, ''):
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


# ================= AUDIT TRAIL (tamper-evident hash chain) =================
def _audit_hash(entry):
    payload = json.dumps({k: entry[k] for k in ('seq', 'ts', 'actor', 'role', 'event', 'details', 'prev_hash')},
                         sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def audit(actor, role, event, details):
    with _write_lock, connect() as conn:
        last = conn.execute('SELECT seq, hash FROM audit_log ORDER BY seq DESC LIMIT 1').fetchone()
        entry = {
            'seq': (last['seq'] + 1) if last else 1,
            'ts': now(),
            'actor': actor or 'unknown',
            'role': role or 'SYSTEM',
            'event': event,
            'details': dumps(details),
            'prev_hash': last['hash'] if last else '0' * 64,
        }
        entry['hash'] = _audit_hash(entry)
        conn.execute('INSERT INTO audit_log (seq, ts, actor, role, event, details, prev_hash, hash) '
                     'VALUES (:seq, :ts, :actor, :role, :event, :details, :prev_hash, :hash)', entry)


def verify_audit_chain():
    prev = '0' * 64
    for entry in query('SELECT * FROM audit_log ORDER BY seq'):
        if entry['prev_hash'] != prev or _audit_hash(entry) != entry['hash']:
            return False, entry['seq']
        prev = entry['hash']
    return True, None
