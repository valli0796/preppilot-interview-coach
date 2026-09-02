from modules.database import get_connection, insert_question
from modules.question_generator import generate_question
import random


SUGGESTED_ROLES = [
    "Python Developer", "Java Developer", "MERN Stack Developer",
    "Data Analyst", "Data Scientist", "Software Tester", "HR Interview",
    "DevOps Engineer", "Machine Learning Engineer", "Frontend Developer",
]

DIFFICULTIES = ["Easy", "Medium", "Hard"]


def rows_to_dicts(cur, rows):
    columns = [desc[0] for desc in cur.description]
    return [dict(zip(columns, row)) for row in rows]


def get_recent_question_texts(
    user_id: int,
    job_role: str,
    limit: int = 15
) -> list:

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT q.question
        FROM interview_results ir
        JOIN questions q
            ON ir.question_id = q.question_id
        WHERE ir.user_id = %s
          AND q.job_role = %s
        ORDER BY ir.date DESC
        LIMIT %s
        """,
        (user_id, job_role, limit),
    )

    rows = cur.fetchall()
    texts = [row[0] for row in rows]

    cur.close()
    conn.close()

    return texts


def get_unanswered_question(
    job_role: str,
    category: str,
    user_id: int
) -> dict | None:

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM questions
        WHERE job_role = %s
          AND category = %s
          AND question_id NOT IN (
              SELECT question_id
              FROM interview_results
              WHERE user_id = %s
          )
        """,
        (job_role, category, user_id),
    )

    rows = rows_to_dicts(cur, cur.fetchall())

    cur.close()
    conn.close()

    if not rows:
        return None

    return random.choice(rows)


def get_next_question(
    job_role: str,
    category: str,
    user_id: int,
    resume_text: str = ""
) -> tuple[dict, bool]:

    existing = get_unanswered_question(
        job_role,
        category,
        user_id
    )

    if existing:
        return existing, False

    avoid = get_recent_question_texts(
        user_id,
        job_role
    )

    generated = generate_question(
        job_role,
        category,
        avoid_questions=avoid,
        resume_text=resume_text
    )

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

    cur.execute(
        """
        SELECT *
        FROM questions
        WHERE job_role = %s
          AND category = %s
        """,
        (job_role, category),
    )

    rows = rows_to_dicts(cur, cur.fetchall())

    cur.close()
    conn.close()

    if rows:
        return random.choice(rows), False

    return None, False


def save_result(
    user_id: int,
    question_id: int,
    answer: str,
    score: float,
    feedback: str,
    matched_keywords: str = "",
    missing_keywords: str = ""
) -> None:

    safe_score = float(score)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO interview_results
        (
            user_id,
            question_id,
            answer,
            score,
            feedback,
            matched_keywords,
            missing_keywords
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            user_id,
            question_id,
            answer,
            safe_score,
            feedback,
            matched_keywords,
            missing_keywords
        ),
    )

    conn.commit()

    cur.close()
    conn.close()


def get_user_results(user_id: int):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            ir.*,
            q.question,
            q.job_role,
            q.category
        FROM interview_results ir
        JOIN questions q
            ON ir.question_id = q.question_id
        WHERE ir.user_id = %s
        ORDER BY ir.date DESC
        """,
        (user_id,),
    )

    rows = rows_to_dicts(cur, cur.fetchall())

    cur.close()
    conn.close()

    return rows

