"""Local SQLite-backed runtime settings management.

This layer stores settings for operational use only. Formal application
configuration still comes from environment variables and app.config.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.config import DATABASE_PATH
from app.services import db

SECRET_KEY_MARKERS = ("API_KEY", "TOKEN", "SECRET", "PASSWORD", "PRIVATE_KEY")


def is_secret_key(key: str) -> bool:
    normalized = str(key or "").upper()
    return any(marker in normalized for marker in SECRET_KEY_MARKERS)


def mask_secret(value: str | None) -> str:
    value = str(value or "")
    if not value:
        return "missing"
    if len(value) <= 4:
        return "configured"
    return f"{value[:4]}****{value[-4:]}"


def _ensure_db(db_path: Path | str | None) -> Path | str:
    selected = db_path if db_path is not None else DATABASE_PATH
    db.init_db(selected)
    return selected


def _row_to_dict(row: Any, reveal_secret: bool = False) -> dict[str, Any]:
    item = dict(row)
    if int(item.get("is_secret") or 0) and not reveal_secret:
        item["value"] = mask_secret(item.get("value"))
    item["is_secret"] = bool(item.get("is_secret"))
    return item


def set_setting(
    key: str,
    value: str,
    is_secret: bool = False,
    description: str = "",
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    if not str(key).strip():
        raise ValueError("Setting key is required")
    selected = _ensure_db(db_path)
    effective_secret = bool(is_secret) or is_secret_key(key)
    with db.get_connection(selected) as connection:
        connection.execute(
            """
            INSERT INTO app_settings (key, value, is_secret, description)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                is_secret = excluded.is_secret,
                description = excluded.description,
                updated_at = CURRENT_TIMESTAMP
            """,
            (str(key).strip(), str(value), int(effective_secret), str(description or "")),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM app_settings WHERE key = ?", (str(key).strip(),)
        ).fetchone()
    return _row_to_dict(row, reveal_secret=True)


def get_setting_record(
    key: str,
    db_path: Path | str | None = None,
    reveal_secret: bool = False,
) -> dict[str, Any] | None:
    selected = _ensure_db(db_path)
    with db.get_connection(selected) as connection:
        row = connection.execute("SELECT * FROM app_settings WHERE key = ?", (key,)).fetchone()
    return _row_to_dict(row, reveal_secret) if row else None


def get_setting(
    key: str,
    default: str | None = None,
    db_path: Path | str | None = None,
    reveal_secret: bool = False,
) -> str | None:
    record = get_setting_record(key, db_path=db_path, reveal_secret=reveal_secret)
    return str(record["value"]) if record else default


def list_settings(
    db_path: Path | str | None = None,
    reveal_secret: bool = False,
) -> list[dict[str, Any]]:
    selected = _ensure_db(db_path)
    with db.get_connection(selected) as connection:
        rows = connection.execute(
            "SELECT * FROM app_settings ORDER BY key ASC"
        ).fetchall()
    return [_row_to_dict(row, reveal_secret) for row in rows]


def delete_setting(key: str, db_path: Path | str | None = None) -> bool:
    selected = _ensure_db(db_path)
    with db.get_connection(selected) as connection:
        cursor = connection.execute("DELETE FROM app_settings WHERE key = ?", (key,))
        connection.commit()
    return cursor.rowcount > 0


def app_settings_status(db_path: Path | str | None = None) -> dict[str, int | bool]:
    selected = db_path if db_path is not None else DATABASE_PATH
    path = Path(selected) if not isinstance(selected, str) or not selected.startswith("file:") else None
    if path is not None and not path.exists():
        return {"ready": False, "count": 0}
    try:
        _ensure_db(selected)
        with db.get_connection(selected) as connection:
            count = connection.execute("SELECT COUNT(*) FROM app_settings").fetchone()[0]
        return {"ready": True, "count": int(count)}
    except Exception:
        return {"ready": False, "count": 0}
