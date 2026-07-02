from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
from typing import Any

from fastapi import Request

from app.services.db import get_connection, init_db

PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 260_000


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac(
            PBKDF2_ALGORITHM,
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _row_to_user(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def create_user(email: str, password: str, display_name: str = "") -> dict[str, Any]:
    init_db()
    normalized_email = normalize_email(email)
    with get_connection() as connection:
        try:
            cursor = connection.execute(
                """
                INSERT INTO users (
                    email,
                    password_hash,
                    display_name,
                    trial_status,
                    plan,
                    monthly_quota,
                    used_quota
                )
                VALUES (?, ?, ?, 'trial', 'trial', 10, 0)
                """,
                (normalized_email, hash_password(password), display_name.strip()),
            )
            connection.commit()
        except sqlite3.IntegrityError as error:
            raise ValueError("email_exists") from error
        return get_user_by_id(int(cursor.lastrowid)) or {}


def get_user_by_email(email: str) -> dict[str, Any] | None:
    init_db()
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (normalize_email(email),),
        ).fetchone()
        return _row_to_user(row)


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    init_db()
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _row_to_user(row)


def authenticate_user(email: str, password: str) -> dict[str, Any] | None:
    user = get_user_by_email(email)
    if not user or not verify_password(password, str(user["password_hash"])):
        return None
    with get_connection() as connection:
        connection.execute(
            "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?",
            (user["id"],),
        )
        connection.commit()
    return get_user_by_id(int(user["id"]))


def login_user(request: Request, user_id: int) -> None:
    request.session["user_id"] = int(user_id)


def logout_user(request: Request) -> None:
    request.session.clear()


def get_current_user(request: Request) -> dict[str, Any] | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    try:
        return get_user_by_id(int(user_id))
    except (TypeError, ValueError):
        logout_user(request)
        return None


def _coerce_quota_value(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(parsed, 0)


def get_remaining_quota(user: dict[str, Any] | None) -> int:
    if not user:
        return 0
    monthly_quota = _coerce_quota_value(user.get("monthly_quota"), 10)
    used_quota = _coerce_quota_value(user.get("used_quota"), 0)
    return max(monthly_quota - used_quota, 0)


def get_user_quota(user_id: int) -> dict[str, int] | None:
    user = get_user_by_id(user_id)
    if not user:
        return None
    monthly_quota = _coerce_quota_value(user.get("monthly_quota"), 10)
    used_quota = _coerce_quota_value(user.get("used_quota"), 0)
    return {
        "monthly_quota": monthly_quota,
        "used_quota": used_quota,
        "remaining_quota": max(monthly_quota - used_quota, 0),
    }


def has_remaining_quota(user_id: int) -> bool:
    quota = get_user_quota(user_id)
    return bool(quota and quota["remaining_quota"] > 0)


def increment_used_quota(user_id: int) -> dict[str, int] | None:
    user = get_user_by_id(user_id)
    if not user:
        return None

    monthly_quota = _coerce_quota_value(user.get("monthly_quota"), 10)
    used_quota = _coerce_quota_value(user.get("used_quota"), 0)
    next_used_quota = min(used_quota + 1, monthly_quota)

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE users
            SET monthly_quota = ?, used_quota = ?
            WHERE id = ?
            """,
            (monthly_quota, next_used_quota, user_id),
        )
        connection.commit()

    return {
        "monthly_quota": monthly_quota,
        "used_quota": next_used_quota,
        "remaining_quota": max(monthly_quota - next_used_quota, 0),
    }
