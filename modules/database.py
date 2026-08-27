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
            reference_answer TEXT,
            source TEXT DEFAULT 'static'
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
    _migrate_add_source_column(conn)
    conn.close()
def _migrate_add_source_column(conn: sqlite3.Connection) -> None:
    """If this DB was created before the 'source' column existed
    (i.e. you already ran the app in an earlier session), add it now
    without losing any existing data."""
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(questions);")
    columns = [row["name"] for row in cur.fetchall()]
    if "source" not in columns:
        cur.execute("ALTER TABLE questions ADD COLUMN source TEXT DEFAULT 'static';")
        conn.commit()
def seed_questions_from_csv(csv_path: Path) -> None:
    import pandas as pd
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM questions WHERE source = 'static';")
    count = cur.fetchone()["c"]
    if count == 0:
        df = pd.read_csv(csv_path)
        df["source"] = "static"
        df.to_sql("questions", conn, if_exists="append", index=False)
    conn.close()
def insert_question(question: str, category: str, job_role: str, difficulty: str,
                     expected_keywords: str, reference_answer: str, source: str = "llm") -> int:
    """Insert a dynamically-generated question so it's tracked like any other
    (appears in history/dashboard, and won't repeat for this user going forward)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO questions (question, category, job_role, difficulty,
                                   expected_keywords, reference_answer, source)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (question, category, job_role, difficulty, expected_keywords, reference_answer, source),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id