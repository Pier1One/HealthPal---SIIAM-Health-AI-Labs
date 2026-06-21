import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY,
    nome TEXT,
    data_nascita TEXT,
    sesso TEXT,
    altezza_cm INTEGER,
    peso_kg REAL
);

CREATE TABLE IF NOT EXISTS condition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    data_diagnosi TEXT,
    attiva INTEGER DEFAULT 1,
    note TEXT
);

CREATE TABLE IF NOT EXISTS medication (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    dosaggio TEXT,
    data_inizio TEXT,
    data_fine TEXT,
    attivo INTEGER DEFAULT 1,
    note TEXT
);

CREATE TABLE IF NOT EXISTS medication_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medication_id INTEGER NOT NULL,
    orario TEXT NOT NULL,
    FOREIGN KEY (medication_id) REFERENCES medication(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS monitoring_task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    frequenza_giorni INTEGER DEFAULT 1,
    orario TEXT,
    note TEXT
);

CREATE TABLE IF NOT EXISTS appointment_task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    specialista TEXT NOT NULL,
    frequenza_giorni INTEGER,
    data_ultima TEXT,
    data_prossima TEXT,
    note TEXT
);

CREATE TABLE IF NOT EXISTS exam_task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    frequenza_giorni INTEGER,
    data_ultima TEXT,
    data_prossima TEXT,
    note TEXT
);

CREATE TABLE IF NOT EXISTS prescription_task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    farmaco TEXT NOT NULL,
    frequenza_giorni INTEGER,
    data_ultima TEXT,
    data_prossima TEXT,
    note TEXT
);

CREATE TABLE IF NOT EXISTS document (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    nome_file TEXT NOT NULL,
    tipo TEXT,
    data_upload TEXT,
    testo_estratto TEXT
);

CREATE TABLE IF NOT EXISTS measurement (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    valore TEXT NOT NULL,
    unita TEXT,
    data TEXT NOT NULL,
    ora TEXT,
    note TEXT
);

CREATE TABLE IF NOT EXISTS notification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    riferimento_id INTEGER,
    messaggio TEXT NOT NULL,
    scheduled_at TEXT NOT NULL,
    sent_at TEXT,
    status TEXT DEFAULT 'pending'
);
"""


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(_SCHEMA)
    # Migration: add data_ultima to prescription_task if missing (existing DBs)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(prescription_task)").fetchall()]
    if "data_ultima" not in cols:
        conn.execute("ALTER TABLE prescription_task ADD COLUMN data_ultima TEXT")
        conn.commit()
        print("[IoDoc] Migration: added data_ultima to prescription_task")
    conn.commit()
    conn.close()
