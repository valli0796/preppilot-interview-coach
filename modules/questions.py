from modules.database import get_connection, insert_question
from modules.question_generator import generate_question
SUGGESTED_ROLES = [
    "Python Developer", "Java Developer", "MERN Stack Developer",
    "Data Analyst", "Data Scientist", "Software Tester", "HR Interview",
    "DevOps Engineer", "Machine Learning Engineer", "Frontend Developer",
]
DIFFICULTIES = ["Easy", "Medium", "Hard"]
def get_answered_question_ids(user_id: int) -> set:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT question_id FROM interview_results WHERE user_id = ?", (user_id,))
    ids = {row["question_id"] for row in cur.fetchall()}
    conn.close()
    return ids
def get_recent_question_texts(user_id: int, job_role: str, limit: int = 15) -> list:
    """Used to tell the LLM what NOT to repeat when generating a new question."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT q.question FROM interview_results ir
           JOIN questions q ON ir.question_id = q.question_id
           WHERE ir.user_id = ? AND q.job_role = ?
           ORDER BY ir.date DESC LIMIT ?""",
        (user_id, job_role, limit),
    )
    texts = [row["question"] for row in cur.fetchall()]
    conn.close()
    return texts
def get_unanswered_question(job_role: str, category: str, user_id: int) -> dict | None:
    """Try to find a static question for this role/category the user hasn't seen yet."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT * FROM questions
           WHERE job_role = ? AND category = ?
           AND question_id NOT IN (
               SELECT question_id FROM interview_results WHERE user_id = ?
           )""",
        (job_role, category, user_id),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    if not rows:
        return None
    import random
    return random.choice(rows)
def get_next_question(job_role: str, category: str, user_id: int) -> tuple[dict, bool]:
    """Main entry point for getting a question to show the user.

    Order of preference:
      1. An unused static question for this exact role/category.
      2. A freshly LLM-generated question (works for ANY role, including
         ones typed in that aren't in the static bank at all).

    Returns (question_dict, was_generated_by_llm).
    """
    existing = get_unanswered_question(job_role, category, user_id)
    if existing:
        return existing, False
    avoid = get_recent_question_texts(user_id, job_role)
    generated = generate_question(job_role, category, avoid_questions=avoid)
    if generated:
        new_id = insert_question(
            question=generated["question"],
            category=category,
            job_role=job_role,
            difficulty=generated["difficulty"],
            expected_keywords=generated["expected_keywords"],
            reference_answer=generated["reference_answer"],
            source="llm",
        )
        generated["question_id"] = new_id
        generated["job_role"] = job_role
        generated["category"] = category
        return generated, True
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM questions WHERE job_role = ? AND category = ?", (job_role, category))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    if rows:
        import random
        return random.choice(rows), False
    return None, False
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