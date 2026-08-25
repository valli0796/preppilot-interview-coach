"""
questions.py
------------
Question retrieval and result-saving logic.
"""

from modules.database import get_connection

JOB_ROLES = ["Python Developer", "Data Analyst", "HR Interview"]
DIFFICULTIES = ["Easy", "Medium", "Hard"]


def get_questions(job_role: str, category: str | None = None, difficulty: str | None = None):
    conn = get_connection()
    cur = conn.cursor()

    query = "SELECT * FROM questions WHERE job_role = ?"
    params: list = [job_role]

    if category:
        query += " AND category = ?"
        params.append(category)
    if difficulty:
        query += " AND difficulty = ?"
        params.append(difficulty)

    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def save_result(user_id: int, question_id: int, answer: str, score: float, feedback: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO interview_results (user_id, question_id, answer, score, feedback)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, question_id, answer, score, feedback),
    )
    conn.commit()
    conn.close()


def get_user_results(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT ir.*, q.question, q.job_role, q.category
           FROM interview_results ir
           JOIN questions q ON ir.question_id = q.question_id
           WHERE ir.user_id = ?
           ORDER BY ir.date DESC""",
        (user_id,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows