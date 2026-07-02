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
    monthly_quota INTEGER NOT NULL DEFAULT 10,
    used_quota INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TEXT
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
        connection.commit()
