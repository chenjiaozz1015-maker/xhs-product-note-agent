from pathlib import Path

from app.services import runtime_config_service, settings_service
from app.services.content_engine_adapter import resolve_content_engine_type
from app.services.llm_content_service import get_llm_config_status
from app.services.settings_service import set_setting


def test_runtime_config_prefers_env_then_app_settings_then_default(tmp_path, monkeypatch):
    database_path = tmp_path / "runtime.sqlite3"
    monkeypatch.setattr(settings_service, "DATABASE_PATH", database_path)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    set_setting("LLM_MODEL", "qwen-plus", db_path=database_path)

    from_settings = runtime_config_service.get_runtime_config_value("LLM_MODEL", "fallback")
    assert from_settings["value"] == "qwen-plus"
    assert from_settings["source"] == "app_settings"

    monkeypatch.setenv("LLM_MODEL", "env-model")
    from_env = runtime_config_service.get_runtime_config_value("LLM_MODEL", "fallback")
    assert from_env["value"] == "env-model"
    assert from_env["source"] == "env"

    monkeypatch.delenv("LLM_MODEL")
    settings_service.delete_setting("LLM_MODEL", db_path=database_path)
    from_default = runtime_config_service.get_runtime_config_value("LLM_MODEL", "fallback")
    assert from_default["value"] == "fallback"
    assert from_default["source"] == "default"


def test_llm_status_reads_app_settings_secret_without_exposing_it(tmp_path, monkeypatch):
    database_path = tmp_path / "runtime.sqlite3"
    monkeypatch.setattr(settings_service, "DATABASE_PATH", database_path)
    for key, value, secret in [
        ("LLM_PROVIDER", "openai_compatible", False),
        ("LLM_API_KEY", "test-secret-value", True),
        ("LLM_BASE_URL", "https://example.com/v1", False),
        ("LLM_MODEL", "demo-model", False),
        ("LLM_TIMEOUT_SECONDS", "15", False),
        ("LLM_MAX_RETRIES", "0", False),
    ]:
        set_setting(key, value, is_secret=secret, db_path=database_path)

    status = get_llm_config_status("llm_openai_compatible")
    assert status.llm_config_ready is True
    assert status.llm_api_key_source == "app_settings"
    assert status.llm_api_key_preview != "test-secret-value"


def test_content_engine_type_can_fallback_to_app_settings(tmp_path, monkeypatch):
    database_path = tmp_path / "runtime.sqlite3"
    monkeypatch.setattr(settings_service, "DATABASE_PATH", database_path)
    monkeypatch.delenv("CONTENT_ENGINE_TYPE", raising=False)
    set_setting("CONTENT_ENGINE_TYPE", "llm_placeholder", db_path=database_path)
    assert resolve_content_engine_type() == "llm_placeholder"
