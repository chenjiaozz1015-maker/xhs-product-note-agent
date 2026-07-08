from __future__ import annotations

from app.services import config_center_client


def test_get_config_center_settings_masks_invite_code(monkeypatch):
    monkeypatch.setenv("CONFIG_CENTER_BASE_URL", "http://39.106.61.160:28081")
    monkeypatch.setenv("CONFIG_CENTER_INVITE_CODE", "super-secret-code")

    settings = config_center_client.get_config_center_settings()

    assert settings["enabled"] is True
    assert settings["project_code"] == "zhongcaoji"
    assert settings["invite_code_status"] == "configured"
    assert settings["invite_code_masked"] != "super-secret-code"


def test_fetch_project_config_returns_not_configured_stub():
    payload = config_center_client.fetch_project_config()

    assert payload["available"] is False
    assert payload["reason"] == "config_center_read_api_not_configured"
