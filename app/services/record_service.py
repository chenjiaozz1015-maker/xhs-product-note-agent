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
    requested_engine_type: str = "",
    content_engine_type: str = "",
    content_fallback_used: bool = False,
    content_fallback_reason: str = "",
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
                quota_cost,
                requested_engine_type,
                content_engine_type,
                content_fallback_used,
                content_fallback_reason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(user_id),
                product_name.strip(),
                category.strip(),
                content_type.strip(),
                style.strip(),
                max(int(image_count), 0),
                max(int(quota_cost), 0),
                requested_engine_type.strip(),
                content_engine_type.strip(),
                1 if content_fallback_used else 0,
                content_fallback_reason.strip(),
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


def get_record_content_engine_label(record: dict[str, Any]) -> str:
    engine_type = str(record.get("content_engine_type") or "").strip()
    fallback_used = bool(record.get("content_fallback_used"))
    requested_engine_type = str(record.get("requested_engine_type") or "").strip()

    if engine_type == "llm_openai_compatible":
        return "LLM 生成"
    if fallback_used and requested_engine_type == "llm_openai_compatible":
        return "规则引擎（已回退）"
    if engine_type == "rule_based":
        return "规则引擎"
    return "旧记录未标注"


def summarize_record_engines(records: list[dict[str, Any]]) -> dict[str, int]:
    total = len(records)
    llm_count = 0
    rule_based_count = 0
    fallback_count = 0

    for record in records:
        engine_type = str(record.get("content_engine_type") or "").strip()
        if engine_type == "llm_openai_compatible":
            llm_count += 1
        elif engine_type == "rule_based":
            rule_based_count += 1

        if bool(record.get("content_fallback_used")):
            fallback_count += 1

    return {
        "total": total,
        "llm_count": llm_count,
        "rule_based_count": rule_based_count,
        "fallback_count": fallback_count,
    }
