from pathlib import Path

from app.services import db
from app.services.settings_service import (
    app_settings_status,
    get_setting,
    get_setting_record,
    list_settings,
    mask_secret,
    set_setting,
)


def test_init_db_creates_app_settings_table(tmp_path: Path):
    database_path = tmp_path / "settings.sqlite3"
    db.init_db(database_path)
    with db.get_connection(database_path) as connection:
        table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='app_settings'"
        ).fetchone()
    assert table[0] == "app_settings"
    assert app_settings_status(database_path) == {"ready": True, "count": 0}


def test_settings_round_trip_and_secret_masking(tmp_path: Path):
    database_path = tmp_path / "settings.sqlite3"
    set_setting("LLM_MODEL", "qwen-plus", db_path=database_path)
    set_setting("LLM_API_KEY", "secret-api-key-1234", db_path=database_path)

    assert get_setting("LLM_MODEL", db_path=database_path) == "qwen-plus"
    assert get_setting("LLM_API_KEY", db_path=database_path) == "secr****1234"
    assert get_setting("LLM_API_KEY", db_path=database_path, reveal_secret=True) == "secret-api-key-1234"
    records = list_settings(db_path=database_path)
    api_record = next(item for item in records if item["key"] == "LLM_API_KEY")
    assert api_record["is_secret"] is True
    assert api_record["value"] == "secr****1234"
    assert mask_secret("") == "missing"
    assert mask_secret("abcd") == "configured"


def test_setting_update_preserves_single_key(tmp_path: Path):
    database_path = tmp_path / "settings.sqlite3"
    set_setting("LLM_MODEL", "old", db_path=database_path)
    set_setting("LLM_MODEL", "new", description="model", db_path=database_path)
    assert get_setting("LLM_MODEL", db_path=database_path) == "new"
    assert len(list_settings(db_path=database_path)) == 1
    assert get_setting_record("LLM_MODEL", db_path=database_path)["description"] == "model"
