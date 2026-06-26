import asyncio

from app.config import APP_VERSION
from app.main import health


def test_health_returns_version_and_directory_status():
    payload = asyncio.run(health())

    assert payload["status"] == "ok"
    assert payload["app"] == "zhongcaoji"
    assert payload["version"] == APP_VERSION
    assert payload["uploads_dir_exists"] is True
    assert payload["generated_dir_exists"] is True
