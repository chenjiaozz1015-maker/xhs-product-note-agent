import asyncio

from app.config import APP_VERSION
from app.main import health


def test_health_returns_version_and_directory_status():
    payload = asyncio.run(health())

    assert payload["status"] == "ok"
    assert payload["app"] == "zhongcaoji"
    assert payload["version"] == APP_VERSION
    assert payload["version"] == "v0.7-3"
    assert payload["content_engine_type"]
    assert payload["poster_engine_type"]
    assert payload["llm_provider"] == "openai_compatible"
    assert "llm_config_ready" in payload
    assert payload["config_center_project_code"] == "zhongcaoji"
    assert payload["config_center_env"] == "test"
    assert "config_center_runtime_token_ready" in payload
    assert "app_settings_ready" in payload
    assert "app_settings_count" in payload
    assert "content_engine_type_source" in payload
    assert "llm_api_key_source" in payload
    assert "llm_api_key_configured" in payload
    assert "runtimeConfigToken" not in payload
    assert payload["uploads_dir_exists"] is True
    assert payload["generated_dir_exists"] is True
    assert payload["static_dir_exists"] is True
    assert payload["css_file_exists"] is True
    assert payload["js_file_exists"] is True
    assert "font_file_exists" in payload
    assert "font_path" in payload
