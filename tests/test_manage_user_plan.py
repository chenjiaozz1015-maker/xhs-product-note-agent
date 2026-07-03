from __future__ import annotations

from pathlib import Path

from app.services import db
from app.services.auth_service import create_user, get_user_by_email, get_user_quota
from scripts.manage_user_plan import main


def _setup_db(monkeypatch, tmp_path: Path) -> Path:
    database_path = tmp_path / "test_manage_user_plan.db"
    monkeypatch.setattr(db, "DATABASE_PATH", database_path)
    db.init_db(database_path)
    return database_path


def test_show_command_displays_user(monkeypatch, tmp_path, capsys):
    database_path = _setup_db(monkeypatch, tmp_path)
    create_user("user@example.com", "secret123", "测试用户")

    exit_code = main(["show", "--email", "user@example.com", "--db", str(database_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "用户信息：" in captured.out
    assert "user@example.com" in captured.out
    assert "Plan: trial" in captured.out


def test_set_plan_personal_syncs_quota_and_keeps_usage(monkeypatch, tmp_path, capsys):
    database_path = _setup_db(monkeypatch, tmp_path)
    user = create_user("user@example.com", "secret123", "测试用户")
    with db.get_connection() as connection:
        connection.execute("UPDATE users SET used_quota = 3 WHERE id = ?", (int(user["id"]),))
        connection.commit()

    exit_code = main(
        ["set-plan", "--email", "user@example.com", "--plan", "personal", "--db", str(database_path)]
    )
    captured = capsys.readouterr()
    updated_user = get_user_by_email("user@example.com")
    quota = get_user_quota(int(updated_user["id"])) if updated_user else None

    assert exit_code == 0
    assert updated_user is not None
    assert updated_user["plan"] == "personal"
    assert quota is not None
    assert quota["monthly_quota"] == 100
    assert quota["used_quota"] == 3
    assert "修改前：" in captured.out
    assert "修改后：" in captured.out
    assert "Plan: personal" in captured.out


def test_set_plan_business_syncs_quota(monkeypatch, tmp_path):
    database_path = _setup_db(monkeypatch, tmp_path)
    create_user("user@example.com", "secret123", "测试用户")

    exit_code = main(
        ["set-plan", "--email", "user@example.com", "--plan", "business", "--db", str(database_path)]
    )
    user = get_user_by_email("user@example.com")
    quota = get_user_quota(int(user["id"])) if user else None

    assert exit_code == 0
    assert user is not None
    assert user["plan"] == "business"
    assert quota is not None
    assert quota["monthly_quota"] == 500


def test_set_plan_rejects_unknown_plan(monkeypatch, tmp_path, capsys):
    database_path = _setup_db(monkeypatch, tmp_path)
    create_user("user@example.com", "secret123", "测试用户")

    exit_code = main(
        ["set-plan", "--email", "user@example.com", "--plan", "credits_100", "--db", str(database_path)]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "当前脚本只支持 trial / personal / business" in captured.err


def test_show_command_reports_missing_user(monkeypatch, tmp_path, capsys):
    database_path = _setup_db(monkeypatch, tmp_path)

    exit_code = main(["show", "--email", "missing@example.com", "--db", str(database_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "未找到用户：missing@example.com" in captured.err


def test_missing_database_reports_friendly_error(tmp_path, capsys):
    missing_path = tmp_path / "missing.db"

    exit_code = main(["show", "--email", "user@example.com", "--db", str(missing_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "未找到数据库文件，请确认已在项目根目录运行，或通过 --db 指定数据库路径。" in captured.err


def test_list_command_displays_recent_users(monkeypatch, tmp_path, capsys):
    database_path = _setup_db(monkeypatch, tmp_path)
    create_user("first@example.com", "secret123", "第一个用户")
    create_user("second@example.com", "secret123", "第二个用户")

    exit_code = main(["list", "--limit", "2", "--db", str(database_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "最近用户：" in captured.out
    assert "first@example.com" in captured.out
    assert "second@example.com" in captured.out
