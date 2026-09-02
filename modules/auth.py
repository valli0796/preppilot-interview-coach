import secrets
import datetime
import bcrypt

from modules.database import get_connection


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(
        password.encode("utf-8"),
        password_hash.encode("utf-8")
    )


def register_user(
    name: str,
    email: str,
    password: str,
    skills: str = "",
    qualification: str = ""
) -> tuple[bool, str]:

    if not name or not email or not password:
        return False, "Name, email, and password are required."

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO users
            (name, email, password_hash, skills, qualification)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                name,
                email.lower().strip(),
                hash_password(password),
                skills,
                qualification
            ),
        )

        conn.commit()
        return True, "Registration successful. Please log in."

    except Exception as e:
        conn.rollback()

        if "duplicate key" in str(e).lower() or "unique" in str(e).lower():
            return False, "An account with this email already exists."

        return False, "Registration failed. Please try again."

    finally:
        cur.close()
        conn.close()


def login_user(
    email: str,
    password: str
) -> tuple[bool, str, dict | None]:

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE email = %s",
        (email.lower().strip(),)
    )

    row = cur.fetchone()

    if row is None:
        cur.close()
        conn.close()
        return False, "No account found with that email.", None

    columns = [desc[0] for desc in cur.description]
    user = dict(zip(columns, row))

    cur.close()
    conn.close()

    if not verify_password(password, user["password_hash"]):
        return False, "Incorrect password.", None

    return True, "Login successful.", user


def create_remember_token(
    user_id: int,
    days: int = 30
) -> str:

    token = secrets.token_urlsafe(32)

    expires_at = (
        datetime.datetime.now()
        + datetime.timedelta(days=days)
    )

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO remember_tokens
        (token, user_id, expires_at)
        VALUES (%s, %s, %s)
        """,
        (
            token,
            user_id,
            expires_at
        ),
    )

    conn.commit()
    cur.close()
    conn.close()

    return token


def get_user_by_remember_token(
    token: str
) -> dict | None:

    if not token:
        return None

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM remember_tokens
        WHERE token = %s
        """,
        (token,)
    )

    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        return None

    columns = [desc[0] for desc in cur.description]
    token_data = dict(zip(columns, row))

    expires_at = token_data["expires_at"]

    if isinstance(expires_at, str):
        expires_at = datetime.datetime.fromisoformat(expires_at)

    if expires_at < datetime.datetime.now():
        cur.execute(
            "DELETE FROM remember_tokens WHERE token = %s",
            (token,)
        )

        conn.commit()
        cur.close()
        conn.close()
        return None

    cur.execute(
        """
        SELECT *
        FROM users
        WHERE user_id = %s
        """,
        (token_data["user_id"],)
    )

    user_row = cur.fetchone()

    if user_row:
        columns = [desc[0] for desc in cur.description]
        user = dict(zip(columns, user_row))
    else:
        user = None

    cur.close()
    conn.close()

    return user


def delete_remember_token(token: str) -> None:

    if not token:
        return

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM remember_tokens WHERE token = %s",
        (token,)
    )

    conn.commit()
    cur.close()
    conn.close()

