import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path


DATABASE_URL = st.secrets["DATABASE_URL"]


def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            skills TEXT,
            qualification TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            question_id SERIAL PRIMARY KEY,
            question TEXT NOT NULL,
            category TEXT,
            job_role TEXT NOT NULL,
            difficulty TEXT,
            expected_keywords TEXT,
            reference_answer TEXT,
            source TEXT DEFAULT 'static'
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS interview_results (
            result_id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            answer TEXT,
            score REAL,
            feedback TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            matched_keywords TEXT DEFAULT '',
            missing_keywords TEXT DEFAULT '',
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (question_id) REFERENCES questions (question_id)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS remember_tokens (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        );
    """)

    conn.commit()
    _migrate_add_source_column(conn)
    _migrate_add_keyword_columns(conn)
    cur.close()
    conn.close()


def _migrate_add_source_column(conn) -> None:
    cur = conn.cursor()

    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'questions';
    """)

    columns = [row[0] for row in cur.fetchall()]

    if "source" not in columns:
        cur.execute("""
            ALTER TABLE questions
            ADD COLUMN source TEXT DEFAULT 'static';
        """)
        conn.commit()

    cur.close()


def _migrate_add_keyword_columns(conn) -> None:
    cur = conn.cursor()

    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'interview_results';
    """)

    columns = [row[0] for row in cur.fetchall()]

    if "matched_keywords" not in columns:
        cur.execute("""
            ALTER TABLE interview_results
            ADD COLUMN matched_keywords TEXT DEFAULT '';
        """)

    if "missing_keywords" not in columns:
        cur.execute("""
            ALTER TABLE interview_results
            ADD COLUMN missing_keywords TEXT DEFAULT '';
        """)

    conn.commit()
    cur.close()


def seed_questions_from_csv(csv_path: Path) -> None:
    import pandas as pd

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT COUNT(*) AS c
        FROM questions
        WHERE source = 'static';
    """)

    count = cur.fetchone()["c"]

    if count == 0:
        df = pd.read_csv(csv_path)
        df["source"] = "static"

        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO questions
                (question, category, job_role, difficulty,
                 expected_keywords, reference_answer, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                row["question"],
                row.get("category"),
                row["job_role"],
                row.get("difficulty"),
                row.get("expected_keywords"),
                row.get("reference_answer"),
                row["source"]
            ))

    conn.commit()
    cur.close()
    conn.close()


def insert_question(
    question: str,
    category: str,
    job_role: str,
    difficulty: str,
    expected_keywords: str,
    reference_answer: str,
    source: str = "llm"
) -> int:

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO questions
        (question, category, job_role, difficulty,
         expected_keywords, reference_answer, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING question_id
        """,
        (
            question,
            category,
            job_role,
            difficulty,
            expected_keywords,
            reference_answer,
            source
        ),
    )

    new_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return new_id