from __future__ import annotations

import importlib.util
import json
import sqlite3
from pathlib import Path

from app.services import db
from app.services.auth_service import create_user
from app.services.record_service import create_generation_record


def _load_module():
    script_path = Path("scripts/engine_usage_report.py")
    spec = importlib.util.spec_from_file_location("engine_usage_report", script_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _setup_current_db(monkeypatch, tmp_path: Path) -> Path:
    database_path = tmp_path / "engine_usage.sqlite3"
    monkeypatch.setattr(db, "DATABASE_PATH", database_path)
    db.init_db(database_path)
    return database_path


def _insert_records() -> tuple[dict, dict]:
    first_user = create_user("user@example.com", "secret123", "User One")
    second_user = create_user("other@example.com", "secret123", "User Two")
    create_generation_record(
        user_id=int(first_user["id"]),
        product_name="cake",
        category="food",
        content_type="review",
        style="gentle",
        requested_engine_type="rule_based",
        content_engine_type="rule_based",
        content_fallback_used=False,
    )
    create_generation_record(
        user_id=int(first_user["id"]),
        product_name="hand cream",
        category="beauty",
        content_type="review",
        style="gentle",
        requested_engine_type="llm_openai_compatible",
        content_engine_type="llm_openai_compatible",
        content_fallback_used=False,
    )
    create_generation_record(
        user_id=int(second_user["id"]),
        product_name="bottle",
        category="home",
        content_type="review",
        style="list",
        requested_engine_type="llm_openai_compatible",
        content_engine_type="rule_based",
        content_fallback_used=True,
        content_fallback_reason="llm_timeout",
    )
    return first_user, second_user


def test_engine_usage_report_default_text_output(monkeypatch, tmp_path, capsys):
    module = _load_module()
    database_path = _setup_current_db(monkeypatch, tmp_path)
    _insert_records()

    exit_code = module.main(["--db", str(database_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Content Engine Usage Report" in captured.out
    assert "Total records: 3" in captured.out
    assert "Rule-based: 2" in captured.out
    assert "LLM: 1" in captured.out
    assert "Fallback: 1" in captured.out
    assert "llm_timeout: 1" in captured.out
    assert "user@example.com" in captured.out
    assert "other@example.com" in captured.out


def test_engine_usage_report_json_output_and_email_filter(monkeypatch, tmp_path, capsys):
    module = _load_module()
    database_path = _setup_current_db(monkeypatch, tmp_path)
    _insert_records()

    exit_code = module.main(
        ["--db", str(database_path), "--email", "user@example.com", "--limit", "2", "--format", "json"]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["scope"] == "user@example.com"
    assert payload["limit"] == 2
    assert payload["summary"]["total_records"] == 2
    assert payload["summary"]["llm"] == 1
    assert payload["summary"]["fallback"] == 0
    assert len(payload["records"]) == 2
    assert all(record["email"] == "user@example.com" for record in payload["records"])


def test_engine_usage_report_missing_database_is_friendly(tmp_path, capsys):
    module = _load_module()
    missing_path = tmp_path / "missing.sqlite3"

    exit_code = module.main(["--db", str(missing_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Database file not found" in captured.err


def test_engine_usage_report_no_records_is_friendly(monkeypatch, tmp_path, capsys):
    module = _load_module()
    database_path = _setup_current_db(monkeypatch, tmp_path)

    exit_code = module.main(["--db", str(database_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "No generation records found for the selected scope." in captured.out


def test_engine_usage_report_handles_old_schema_without_engine_columns(tmp_path, capsys):
    module = _load_module()
    database_path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
            """
        )
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
        connection.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            ("legacy@example.com", "hash"),
        )
        connection.execute(
            """
            INSERT INTO generation_records (user_id, product_name, category, content_type, style)
            VALUES (?, ?, ?, ?, ?)
            """,
            (1, "legacy item", "legacy category", "legacy content", "legacy style"),
        )
        connection.commit()

    exit_code = module.main(["--db", str(database_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["summary"]["unknown"] == 1
    assert payload["records"][0]["content_engine_type"] == ""
    assert payload["records"][0]["fallback_used"] is False


def test_engine_usage_report_is_read_only(monkeypatch, tmp_path, capsys):
    module = _load_module()
    database_path = _setup_current_db(monkeypatch, tmp_path)
    _insert_records()

    with sqlite3.connect(database_path) as connection:
        before_count = connection.execute("SELECT COUNT(*) FROM generation_records").fetchone()[0]

    exit_code = module.main(["--db", str(database_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    with sqlite3.connect(database_path) as connection:
        after_count = connection.execute("SELECT COUNT(*) FROM generation_records").fetchone()[0]

    assert exit_code == 0
    assert before_count == after_count == payload["summary"]["total_records"]
    assert "password_hash" not in json.dumps(payload, ensure_ascii=False)
    assert "sk-" not in json.dumps(payload, ensure_ascii=False)
