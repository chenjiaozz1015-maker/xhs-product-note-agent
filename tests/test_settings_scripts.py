from pathlib import Path
import importlib.util

from app.services import db
from app.services.settings_service import get_setting


def _load(name: str):
    path = Path("scripts") / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_settings_set_get_list_scripts(tmp_path, capsys):
    database_path = tmp_path / "settings.sqlite3"
    settings_set = _load("settings_set")
    settings_get = _load("settings_get")
    settings_list = _load("settings_list")

    assert settings_set.main([
        "--key", "LLM_API_KEY", "--value", "real-secret-value", "--db", str(database_path), "--secret"
    ]) == 0
    saved_output = capsys.readouterr().out
    assert "real-secret-value" not in saved_output
    assert get_setting("LLM_API_KEY", db_path=database_path, reveal_secret=True) == "real-secret-value"

    assert settings_get.main(["--key", "LLM_API_KEY", "--db", str(database_path)]) == 0
    masked_output = capsys.readouterr().out
    assert "real-secret-value" not in masked_output
    assert "LLM_API_KEY" in masked_output

    assert settings_list.main(["--db", str(database_path)]) == 0
    listed_output = capsys.readouterr().out
    assert "real-secret-value" not in listed_output
    assert "LLM_API_KEY" in listed_output


def test_settings_get_missing_is_friendly(tmp_path, capsys):
    settings_get = _load("settings_get")
    result = settings_get.main(["--key", "LLM_MODEL", "--db", str(tmp_path / "missing.sqlite3")])
    assert result == 1
    assert "Setting not found: LLM_MODEL" in capsys.readouterr().out
