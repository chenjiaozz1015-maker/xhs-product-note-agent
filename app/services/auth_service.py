from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Request

from app.services.db import get_connection, init_db
from app.services.plan_service import (
    DEFAULT_PLAN_CODE,
    get_default_trial_plan,
    get_plan_config,
    get_plan_period_days,
    get_plan_quota,
    normalize_plan_code,
)

PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 260_000


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _format_quota_reset_at(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_quota_reset_at(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        raw_value = str(value)
        if raw_value.endswith("Z"):
            raw_value = raw_value[:-1] + "+00:00"
        parsed = datetime.fromisoformat(raw_value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _next_quota_reset_at(now: datetime | None = None, period_days: int | None = None) -> datetime:
    trial_plan = get_default_trial_plan()
    resolved_period_days = period_days or int(trial_plan["period_days"])
    return (now or _utc_now()) + timedelta(days=resolved_period_days)


def _quota_reset_date(value: str) -> str:
    parsed = _parse_quota_reset_at(value)
    return parsed.date().isoformat() if parsed else ""


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
    trial_plan = get_default_trial_plan()
    monthly_quota = int(trial_plan["quota"])
    period_days = int(trial_plan["period_days"])
    quota_reset_at = _format_quota_reset_at(_next_quota_reset_at(period_days=period_days))
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
                    used_quota,
                    quota_reset_at
                )
                VALUES (?, ?, ?, 'trial', ?, ?, 0, ?)
                """,
                (
                    normalized_email,
                    hash_password(password),
                    display_name.strip(),
                    DEFAULT_PLAN_CODE,
                    monthly_quota,
                    quota_reset_at,
                ),
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


def _quota_default_for_plan(plan_code: str | None) -> int:
    return get_plan_quota(normalize_plan_code(plan_code)) or int(get_default_trial_plan()["quota"])


def _period_days_for_plan(plan_code: str | None) -> int:
    return get_plan_period_days(normalize_plan_code(plan_code)) or int(get_default_trial_plan()["period_days"])


def normalize_user_plan(plan_code: str | None) -> str:
    return normalize_plan_code(plan_code)


def get_effective_plan_config(user: dict[str, Any] | None) -> dict[str, Any]:
    if not user:
        return get_default_trial_plan()
    return get_plan_config(normalize_user_plan(user.get("plan")))


def sync_user_quota_with_plan(user_id: int) -> dict[str, Any] | None:
    user = get_user_by_id(user_id)
    if not user:
        return None

    effective_plan_code = normalize_user_plan(user.get("plan"))
    expected_quota = _quota_default_for_plan(effective_plan_code)
    monthly_quota = _coerce_quota_value(user.get("monthly_quota"), expected_quota)
    used_quota = _coerce_quota_value(user.get("used_quota"), 0)
    quota_reset_at = _parse_quota_reset_at(user.get("quota_reset_at"))
    period_days = _period_days_for_plan(effective_plan_code)
    now = _utc_now()

    if monthly_quota != expected_quota:
        monthly_quota = expected_quota
    if quota_reset_at is None:
        quota_reset_at = _next_quota_reset_at(now, period_days=period_days)
    elif now >= quota_reset_at:
        used_quota = 0
        monthly_quota = expected_quota
        quota_reset_at = _next_quota_reset_at(now, period_days=period_days)

    quota_reset_at_text = _format_quota_reset_at(quota_reset_at)
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE users
            SET monthly_quota = ?, used_quota = ?, quota_reset_at = ?
            WHERE id = ?
            """,
            (monthly_quota, used_quota, quota_reset_at_text, user_id),
        )
        connection.commit()

    return {
        **user,
        "effective_plan_code": effective_plan_code,
        "monthly_quota": monthly_quota,
        "used_quota": used_quota,
        "quota_reset_at": quota_reset_at_text,
    }


def get_remaining_quota(user: dict[str, Any] | None) -> int:
    if not user:
        return 0
    monthly_quota = _coerce_quota_value(
        user.get("monthly_quota"),
        _quota_default_for_plan(str(user.get("plan") or DEFAULT_PLAN_CODE)),
    )
    used_quota = _coerce_quota_value(user.get("used_quota"), 0)
    return max(monthly_quota - used_quota, 0)


def ensure_user_quota_state(user_id: int) -> dict[str, Any] | None:
    user = sync_user_quota_with_plan(user_id)
    if not user:
        return None
    return user


def reset_quota_if_needed(user_id: int) -> dict[str, Any] | None:
    return ensure_user_quota_state(user_id)


def get_user_quota(user_id: int) -> dict[str, Any] | None:
    user = ensure_user_quota_state(user_id)
    if not user:
        return None
    monthly_quota = _coerce_quota_value(
        user.get("monthly_quota"),
        _quota_default_for_plan(str(user.get("plan") or DEFAULT_PLAN_CODE)),
    )
    used_quota = _coerce_quota_value(user.get("used_quota"), 0)
    quota_reset_at = str(user["quota_reset_at"])
    return {
        "monthly_quota": monthly_quota,
        "used_quota": used_quota,
        "remaining_quota": max(monthly_quota - used_quota, 0),
        "plan_code": str(user.get("effective_plan_code") or normalize_user_plan(user.get("plan"))),
        "quota_reset_at": quota_reset_at,
        "quota_reset_date": _quota_reset_date(quota_reset_at),
    }


def has_remaining_quota(user_id: int) -> bool:
    quota = get_user_quota(user_id)
    return bool(quota and quota["remaining_quota"] > 0)


def increment_used_quota(user_id: int) -> dict[str, Any] | None:
    user = ensure_user_quota_state(user_id)
    if not user:
        return None

    monthly_quota = _coerce_quota_value(user.get("monthly_quota"), 10)
    used_quota = _coerce_quota_value(user.get("used_quota"), 0)
    next_used_quota = min(used_quota + 1, monthly_quota)

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE users
            SET monthly_quota = ?, used_quota = ?, quota_reset_at = ?
            WHERE id = ?
            """,
            (monthly_quota, next_used_quota, user["quota_reset_at"], user_id),
        )
        connection.commit()

    return {
        "monthly_quota": monthly_quota,
        "used_quota": next_used_quota,
        "remaining_quota": max(monthly_quota - next_used_quota, 0),
        "quota_reset_at": user["quota_reset_at"],
        "quota_reset_date": _quota_reset_date(str(user["quota_reset_at"])),
    }


def get_quota_summary(user_id: int) -> dict[str, Any] | None:
    return get_user_quota(user_id)
