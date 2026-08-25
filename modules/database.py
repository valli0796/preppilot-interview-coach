"""
database.py
------------
Handles the SQLite connection and schema creation for the
AI-Based Interview Preparation System.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "interview_prep.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            skills TEXT,
            qualification TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            question_id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            category TEXT,
            job_role TEXT NOT NULL,
            difficulty TEXT,
            expected_keywords TEXT,
            reference_answer TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS interview_results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            answer TEXT,
            score REAL,
            feedback TEXT,
            date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (question_id) REFERENCES questions (question_id)
        );
    """)

    conn.commit()
    conn.close()


def seed_questions_from_csv(csv_path: Path) -> None:
    import pandas as pd

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM questions;")
    count = cur.fetchone()["c"]

    if count == 0:
        df = pd.read_csv(csv_path)
        df.to_sql("questions", conn, if_exists="append", index=False)

    conn.close()