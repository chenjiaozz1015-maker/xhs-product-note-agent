from app.services import db
from app.services.record_service import (
    create_generation_record,
    get_record_content_engine_label,
    list_user_generation_records,
    summarize_record_engines,
)


def test_init_db_adds_generation_record_engine_columns(tmp_path, monkeypatch):
    database_path = tmp_path / "records.sqlite3"
    monkeypatch.setattr(db, "DATABASE_PATH", database_path)

    with db.get_connection(database_path) as connection:
        connection.execute(db.USER_TABLE_SQL)
        connection.execute(
            """
            CREATE TABLE generation_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_name TEXT,
                category TEXT,
                content_type TEXT,
                style TEXT,
                image_count INTEGER NOT NULL DEFAULT 3,
                quota_cost INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()

    db.init_db(database_path)

    with db.get_connection(database_path) as connection:
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(generation_records)").fetchall()
        }

    assert "requested_engine_type" in columns
    assert "content_engine_type" in columns
    assert "content_fallback_used" in columns
    assert "content_fallback_reason" in columns


def test_create_generation_record_persists_engine_metadata(tmp_path, monkeypatch):
    database_path = tmp_path / "records.sqlite3"
    monkeypatch.setattr(db, "DATABASE_PATH", database_path)
    db.init_db(database_path)

    with db.get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO users (
                email, password_hash, display_name, trial_status, plan, monthly_quota, used_quota, quota_reset_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("user@example.com", "hashed", "User", "trial", "trial", 10, 0, "2026-08-01T00:00:00Z"),
        )
        user_id = int(cursor.lastrowid)
        connection.commit()

    create_generation_record(
        user_id=user_id,
        product_name="product",
        category="category",
        content_type="content",
        style="style",
        requested_engine_type="llm_openai_compatible",
        content_engine_type="rule_based",
        content_fallback_used=True,
        content_fallback_reason="llm_timeout",
    )

    records = list_user_generation_records(user_id, limit=5)

    assert len(records) == 1
    assert records[0]["requested_engine_type"] == "llm_openai_compatible"
    assert records[0]["content_engine_type"] == "rule_based"
    assert records[0]["content_fallback_used"] == 1
    assert records[0]["content_fallback_reason"] == "llm_timeout"


def test_record_engine_helpers_handle_old_and_fallback_records():
    legacy_record = {}
    rule_record = {"content_engine_type": "rule_based", "content_fallback_used": 0}
    llm_record = {"content_engine_type": "llm_openai_compatible", "content_fallback_used": 0}
    fallback_record = {
        "requested_engine_type": "llm_openai_compatible",
        "content_engine_type": "rule_based",
        "content_fallback_used": 1,
    }

    assert get_record_content_engine_label(legacy_record) == "\u65e7\u8bb0\u5f55\u672a\u6807\u6ce8"
    assert get_record_content_engine_label(rule_record) == "\u89c4\u5219\u5f15\u64ce"
    assert get_record_content_engine_label(llm_record) == "LLM \u751f\u6210"
    assert get_record_content_engine_label(fallback_record) == "\u89c4\u5219\u5f15\u64ce\uff08\u5df2\u56de\u9000\uff09"

    summary = summarize_record_engines([legacy_record, rule_record, llm_record, fallback_record])

    assert summary == {
        "total": 4,
        "llm_count": 1,
        "rule_based_count": 2,
        "fallback_count": 1,
    }
