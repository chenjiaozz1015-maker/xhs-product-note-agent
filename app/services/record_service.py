from __future__ import annotations

import sqlite3
from typing import Any

from app.services.db import get_connection, init_db


def _row_to_record(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def create_generation_record(
    *,
    user_id: int,
    product_name: str,
    category: str,
    content_type: str,
    style: str,
    image_count: int = 3,
    quota_cost: int = 1,
) -> dict[str, Any]:
    init_db()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO generation_records (
                user_id,
                product_name,
                category,
                content_type,
                style,
                image_count,
                quota_cost
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(user_id),
                product_name.strip(),
                category.strip(),
                content_type.strip(),
                style.strip(),
                max(int(image_count), 0),
                max(int(quota_cost), 0),
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM generation_records WHERE id = ?",
            (int(cursor.lastrowid),),
        ).fetchone()
        return _row_to_record(row)


def list_user_generation_records(user_id: int, limit: int = 30) -> list[dict[str, Any]]:
    init_db()
    safe_limit = max(1, min(int(limit), 100))
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM generation_records
            WHERE user_id = ?
            ORDER BY datetime(created_at) DESC, id DESC
            LIMIT ?
            """,
            (int(user_id), safe_limit),
        ).fetchall()
        return [_row_to_record(row) for row in rows]


def list_recent_generation_records(user_id: int, limit: int = 5) -> list[dict[str, Any]]:
    return list_user_generation_records(user_id, limit=limit)
