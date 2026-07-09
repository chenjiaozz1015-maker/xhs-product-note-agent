from __future__ import annotations

from pathlib import Path

from app.services import db
from app.services.auth_service import create_user, get_user_by_email, verify_password
from app.services.record_service import create_generation_record
from scripts.reset_user_password import main


def _setup_db(monkeypatch, tmp_path: Path) -> Path:
    database_path = tmp_path / "test_reset_user_password.db"
    monkeypatch.setattr(db, "DATABASE_PATH", database_path)
    db.init_db(database_path)
    return database_path


def test_reset_password_reports_missing_database(tmp_path, capsys):
    missing_path = tmp_path / "missing.db"

    exit_code = main(["--email", "user@example.com", "--password", "NewPassword123", "--db", str(missing_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert f"Database not found: {missing_path}" in captured.err


def test_reset_password_reports_missing_user(monkeypatch, tmp_path, capsys):
    database_path = _setup_db(monkeypatch, tmp_path)

    exit_code = main(["--email", "missing@example.com", "--password", "NewPassword123", "--db", str(database_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "User not found: missing@example.com" in captured.err


def test_reset_password_rejects_short_password(monkeypatch, tmp_path, capsys):
    database_path = _setup_db(monkeypatch, tmp_path)
    create_user("user@example.com", "secret123", "Test User")

    exit_code = main(["--email", "user@example.com", "--password", "12345", "--db", str(database_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Password must be at least 6 characters" in captured.err


def test_reset_password_updates_hash_and_preserves_user_state(monkeypatch, tmp_path, capsys):
    database_path = _setup_db(monkeypatch, tmp_path)
    user = create_user("user@example.com", "secret123", "Test User")
    assert user

    with db.get_connection() as connection:
        connection.execute(
            "UPDATE users SET plan = ?, monthly_quota = ?, used_quota = ?, quota_reset_at = ? WHERE id = ?",
            ("personal", 100, 7, "2026-08-01T00:00:00Z", int(user["id"])),
        )
        connection.commit()

    create_generation_record(
        user_id=int(user["id"]),
        product_name="sample product",
        category="sample category",
        content_type="sample content",
        style="sample style",
    )

    before_user = get_user_by_email("user@example.com")
    assert before_user is not None
    before_hash = str(before_user["password_hash"])

    exit_code = main(
        ["--email", "user@example.com", "--password", "NewPassword123", "--db", str(database_path)]
    )
    captured = capsys.readouterr()
    after_user = get_user_by_email("user@example.com")

    assert exit_code == 0
    assert "Password reset succeeded for user@example.com" in captured.out
    assert "NewPassword123" not in captured.out
    assert "NewPassword123" not in captured.err
    assert after_user is not None
    assert str(after_user["password_hash"]) != before_hash
    assert str(after_user["password_hash"]) != "NewPassword123"
    assert verify_password("NewPassword123", str(after_user["password_hash"])) is True
    assert after_user["plan"] == "personal"
    assert after_user["monthly_quota"] == 100
    assert after_user["used_quota"] == 7
    assert after_user["quota_reset_at"] == "2026-08-01T00:00:00Z"

    with db.get_connection() as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM generation_records WHERE user_id = ?", (int(user["id"]),)).fetchone()
        assert row is not None
        assert int(row["count"]) == 1
