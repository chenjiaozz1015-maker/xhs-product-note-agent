from __future__ import annotations

import json
import os
from pathlib import Path
from urllib import error, request

from app.config import BASE_DIR

DEFAULT_CONFIG_CENTER_BASE_URL = "http://39.106.61.160:28081"
DEFAULT_CONFIG_CENTER_PROJECT_CODE = "zhongcaoji"
DEFAULT_CONFIG_CENTER_ENV = "test"
DEFAULT_CONFIG_CENTER_RUNTIME_TOKEN_FILE = ".config-center/test.runtime-token.json"
DEFAULT_CONFIG_CENTER_TIMEOUT_SECONDS = 10.0


def mask_sensitive_value(value: str | None) -> str:
    if not value:
        return "missing"
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}***{value[-2:]}"


def _get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _safe_float(value: str, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_config_center_base_url() -> str:
    return _get_env("CONFIG_CENTER_BASE_URL", DEFAULT_CONFIG_CENTER_BASE_URL).rstrip("/")


def build_runtime_token_file_path() -> Path:
    raw_path = _get_env("CONFIG_CENTER_RUNTIME_TOKEN_FILE", DEFAULT_CONFIG_CENTER_RUNTIME_TOKEN_FILE)
    token_path = Path(raw_path)
    return token_path if token_path.is_absolute() else BASE_DIR / token_path


def build_runtime_config_url(settings: dict[str, object] | None = None) -> str:
    settings = settings or get_config_center_settings()
    base_url = str(settings["base_url"]).rstrip("/")
    project_code = str(settings["project_code"])
    env_name = str(settings["env"])
    return f"{base_url}/internal/config-center/v1/projects/{project_code}/runtime-config?env={env_name}"


def is_config_center_enabled() -> bool:
    return bool(build_config_center_base_url())


def get_config_center_settings() -> dict[str, object]:
    timeout_raw = _get_env("CONFIG_CENTER_TIMEOUT_SECONDS", str(DEFAULT_CONFIG_CENTER_TIMEOUT_SECONDS))
    runtime_token_file = build_runtime_token_file_path()
    return {
        "enabled": is_config_center_enabled(),
        "base_url": build_config_center_base_url(),
        "project_code": _get_env("CONFIG_CENTER_PROJECT_CODE", DEFAULT_CONFIG_CENTER_PROJECT_CODE)
        or DEFAULT_CONFIG_CENTER_PROJECT_CODE,
        "env": _get_env("CONFIG_CENTER_ENV", DEFAULT_CONFIG_CENTER_ENV) or DEFAULT_CONFIG_CENTER_ENV,
        "runtime_token_file": str(runtime_token_file.relative_to(BASE_DIR)) if runtime_token_file.is_relative_to(BASE_DIR) else str(runtime_token_file),
        "timeout_seconds": _safe_float(timeout_raw, DEFAULT_CONFIG_CENTER_TIMEOUT_SECONDS),
    }


def load_runtime_config_token() -> dict[str, object]:
    token_path = build_runtime_token_file_path()
    if not token_path.exists():
        return {
            "available": False,
            "runtime_token_ready": False,
            "error": "runtime_token_file_missing",
        }

    try:
        payload = json.loads(token_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "available": False,
            "runtime_token_ready": False,
            "error": "runtime_token_invalid_json",
        }

    token = str(payload.get("runtimeConfigToken", "")).strip() if isinstance(payload, dict) else ""
    if not token:
        return {
            "available": False,
            "runtime_token_ready": False,
            "error": "runtime_token_missing",
        }

    return {
        "available": True,
        "runtime_token_ready": True,
        "error": "",
        "token": token,
    }


def get_runtime_token_summary() -> dict[str, object]:
    token_result = load_runtime_config_token()
    return {
        "runtime_token_ready": bool(token_result.get("runtime_token_ready")),
        "error": str(token_result.get("error", "")),
    }


def _request_runtime_config(url: str, token: str, timeout_seconds: float) -> tuple[int, str]:
    req = request.Request(
        url,
        headers={"X-Project-Config-Token": token},
        method="GET",
    )
    with request.urlopen(req, timeout=timeout_seconds) as response:
        return int(response.getcode()), response.read().decode("utf-8", errors="replace")


def fetch_project_config() -> dict[str, object]:
    settings = get_config_center_settings()
    token_result = load_runtime_config_token()
    if not token_result["available"]:
        return {
            "available": False,
            "project_code": settings["project_code"],
            "env": settings["env"],
            "status_code": None,
            "config": {},
            "error": token_result["error"],
        }

    url = build_runtime_config_url(settings)
    timeout_seconds = float(settings["timeout_seconds"])
    token = str(token_result["token"])

    try:
        status_code, body = _request_runtime_config(url, token, timeout_seconds)
    except error.HTTPError as exc:
        return {
            "available": False,
            "project_code": settings["project_code"],
            "env": settings["env"],
            "status_code": int(exc.code),
            "config": {},
            "error": "runtime_config_http_error",
        }
    except error.URLError:
        return {
            "available": False,
            "project_code": settings["project_code"],
            "env": settings["env"],
            "status_code": None,
            "config": {},
            "error": "runtime_config_request_failed",
        }
    except Exception:
        return {
            "available": False,
            "project_code": settings["project_code"],
            "env": settings["env"],
            "status_code": None,
            "config": {},
            "error": "runtime_config_request_failed",
        }

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return {
            "available": False,
            "project_code": settings["project_code"],
            "env": settings["env"],
            "status_code": status_code,
            "config": {},
            "error": "runtime_config_invalid_json",
        }

    if not isinstance(payload, dict):
        return {
            "available": False,
            "project_code": settings["project_code"],
            "env": settings["env"],
            "status_code": status_code,
            "config": {},
            "error": "runtime_config_invalid_json",
        }

    return {
        "available": True,
        "project_code": settings["project_code"],
        "env": settings["env"],
        "status_code": status_code,
        "config": payload,
        "error": "",
    }
