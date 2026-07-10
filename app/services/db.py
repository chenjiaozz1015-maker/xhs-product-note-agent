from __future__ import annotations

import sqlite3
from pathlib import Path

from app.config import DATABASE_PATH

_SHARED_CONNECTIONS: dict[str, sqlite3.Connection] = {}


USER_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    trial_status TEXT NOT NULL DEFAULT 'trial',
    plan TEXT NOT NULL DEFAULT 'trial',
    monthly_quota INTEGER DEFAULT 10,
    used_quota INTEGER DEFAULT 0,
    quota_reset_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TEXT
)
"""

GENERATION_RECORDS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS generation_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_name TEXT,
    category TEXT,
    content_type TEXT,
    style TEXT,
    image_count INTEGER NOT NULL DEFAULT 3,
    quota_cost INTEGER NOT NULL DEFAULT 1,
    requested_engine_type TEXT,
    content_engine_type TEXT,
    content_fallback_used INTEGER NOT NULL DEFAULT 0,
    content_fallback_reason TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
"""

APP_SETTINGS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS app_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    is_secret INTEGER NOT NULL DEFAULT 0,
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


def get_connection(database_path: Path | str | None = None) -> sqlite3.Connection:
    selected_path = database_path if database_path is not None else DATABASE_PATH
    if isinstance(selected_path, str) and selected_path.startswith("file:"):
        connection = _SHARED_CONNECTIONS.get(selected_path)
        if connection is None:
            connection = sqlite3.connect(selected_path, uri=True)
            connection.row_factory = sqlite3.Row
            _SHARED_CONNECTIONS[selected_path] = connection
        return connection

    path = Path(selected_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(database_path: Path | str | None = None) -> None:
    with get_connection(database_path) as connection:
        connection.execute(USER_TABLE_SQL)
        user_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(users)").fetchall()
        }
        if "quota_reset_at" not in user_columns:
            connection.execute("ALTER TABLE users ADD COLUMN quota_reset_at TEXT")
        connection.execute(GENERATION_RECORDS_TABLE_SQL)
        record_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(generation_records)").fetchall()
        }
        record_column_statements = {
            "requested_engine_type": "ALTER TABLE generation_records ADD COLUMN requested_engine_type TEXT",
            "content_engine_type": "ALTER TABLE generation_records ADD COLUMN content_engine_type TEXT",
            "content_fallback_used": (
                "ALTER TABLE generation_records ADD COLUMN content_fallback_used INTEGER NOT NULL DEFAULT 0"
            ),
            "content_fallback_reason": "ALTER TABLE generation_records ADD COLUMN content_fallback_reason TEXT",
        }
        for column_name, statement in record_column_statements.items():
            if column_name not in record_columns:
                connection.execute(statement)
        connection.execute(APP_SETTINGS_TABLE_SQL)
        connection.commit()
