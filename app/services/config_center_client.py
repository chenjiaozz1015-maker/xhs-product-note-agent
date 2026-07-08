from __future__ import annotations

import os

from app.config import BASE_DIR

DEFAULT_CONFIG_CENTER_BASE_URL = "http://39.106.61.160:28081"
DEFAULT_CONFIG_CENTER_PROJECT_CODE = "zhongcaoji"
DEFAULT_CONFIG_CENTER_RUNTIME = "python"
DEFAULT_CONFIG_CENTER_LOCAL_WORKSPACE_ROOT = str(BASE_DIR)


def mask_sensitive_value(value: str | None) -> str:
    if not value:
        return "missing"
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}***{value[-2:]}"


def build_config_center_base_url() -> str:
    return os.getenv("CONFIG_CENTER_BASE_URL", DEFAULT_CONFIG_CENTER_BASE_URL).strip().rstrip("/")


def is_config_center_enabled() -> bool:
    return bool(build_config_center_base_url())


def get_config_center_settings() -> dict[str, object]:
    invite_code = os.getenv("CONFIG_CENTER_INVITE_CODE", "").strip()
    return {
        "enabled": is_config_center_enabled(),
        "base_url": build_config_center_base_url(),
        "project_code": os.getenv("CONFIG_CENTER_PROJECT_CODE", DEFAULT_CONFIG_CENTER_PROJECT_CODE).strip()
        or DEFAULT_CONFIG_CENTER_PROJECT_CODE,
        "runtime": os.getenv("CONFIG_CENTER_RUNTIME", DEFAULT_CONFIG_CENTER_RUNTIME).strip()
        or DEFAULT_CONFIG_CENTER_RUNTIME,
        "local_workspace_root": os.getenv(
            "CONFIG_CENTER_LOCAL_WORKSPACE_ROOT",
            DEFAULT_CONFIG_CENTER_LOCAL_WORKSPACE_ROOT,
        ).strip()
        or DEFAULT_CONFIG_CENTER_LOCAL_WORKSPACE_ROOT,
        "invite_code_status": "configured" if invite_code else "missing",
        "invite_code_masked": mask_sensitive_value(invite_code),
    }


def fetch_project_config() -> dict[str, object]:
    return {
        "enabled": is_config_center_enabled(),
        "available": False,
        "reason": "config_center_read_api_not_configured",
    }
