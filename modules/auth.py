import sqlite3
import secrets
import datetime
import bcrypt

from modules.database import get_connection


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def register_user(name: str, email: str, password: str, skills: str = "", qualification: str = "") -> tuple[bool, str]:
    if not name or not email or not password:
        return False, "Name, email, and password are required."

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO users (name, email, password_hash, skills, qualification)
               VALUES (?, ?, ?, ?, ?)""",
            (name, email.lower().strip(), hash_password(password), skills, qualification),
        )
        conn.commit()
        return True, "Registration successful. Please log in."
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."
    finally:
        conn.close()


def login_user(email: str, password: str) -> tuple[bool, str, dict | None]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
    row = cur.fetchone()
    conn.close()

    if row is None:
        return False, "No account found with that email.", None

    if not verify_password(password, row["password_hash"]):
        return False, "Incorrect password.", None

    return True, "Login successful.", dict(row)


def create_remember_token(user_id: int, days: int = 30) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.datetime.now() + datetime.timedelta(days=days)).isoformat()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO remember_tokens (token, user_id, expires_at) VALUES (?, ?, ?)",
        (token, user_id, expires_at),
    )
    conn.commit()
    conn.close()
    return token


def get_user_by_remember_token(token: str) -> dict | None:
    if not token:
        return None

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM remember_tokens WHERE token = ?", (token,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return None

    if datetime.datetime.fromisoformat(row["expires_at"]) < datetime.datetime.now():
        cur.execute("DELETE FROM remember_tokens WHERE token = ?", (token,))
        conn.commit()
        conn.close()
        return None

    cur.execute("SELECT * FROM users WHERE user_id = ?", (row["user_id"],))
    user_row = cur.fetchone()
    conn.close()
    return dict(user_row) if user_row else None


def delete_remember_token(token: str) -> None:
    if not token:
        return
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM remember_tokens WHERE token = ?", (token,))
    conn.commit()
    conn.close()