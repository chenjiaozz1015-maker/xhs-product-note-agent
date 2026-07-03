import asyncio

from app.config import APP_VERSION
from app.main import health


def test_health_returns_version_and_directory_status():
    payload = asyncio.run(health())

    assert payload["status"] == "ok"
    assert payload["app"] == "zhongcaoji"
    assert payload["version"] == APP_VERSION
    assert payload["version"] == "v0.3-5"
    assert payload["uploads_dir_exists"] is True
    assert payload["generated_dir_exists"] is True
    assert payload["static_dir_exists"] is True
    assert payload["css_file_exists"] is True
    assert payload["js_file_exists"] is True
    assert "font_file_exists" in payload
    assert "font_path" in payload
