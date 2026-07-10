"""Runtime configuration resolution.

Precedence is intentionally explicit: non-empty environment variable,
local app_settings, then the caller-provided code default.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from app.services.settings_service import get_setting_record, is_secret_key


def get_runtime_config_value(
    key: str,
    default: Any = None,
    db_path: Path | str | None = None,
    reveal_secret: bool = False,
) -> dict[str, Any]:
    env_value = os.getenv(key, "").strip()
    if env_value:
        return {
            "key": key,
            "value": env_value if (reveal_secret or not is_secret_key(key)) else "configured",
            "source": "env",
            "is_secret": is_secret_key(key),
        }

    record = get_setting_record(key, db_path=db_path, reveal_secret=reveal_secret)
    if record:
        value = record.get("value")
        return {
            "key": key,
            "value": value if (reveal_secret or not record.get("is_secret")) else "configured",
            "source": "app_settings",
            "is_secret": bool(record.get("is_secret")),
        }

    if default is not None and str(default).strip() != "":
        return {"key": key, "value": default, "source": "default", "is_secret": False}
    return {"key": key, "value": default, "source": "missing", "is_secret": False}


def get_runtime_config_values(
    keys: list[str],
    defaults: dict[str, Any] | None = None,
    db_path: Path | str | None = None,
    reveal_secret: bool = False,
) -> dict[str, dict[str, Any]]:
    defaults = defaults or {}
    return {
        key: get_runtime_config_value(
            key,
            default=defaults.get(key),
            db_path=db_path,
            reveal_secret=reveal_secret,
        )
        for key in keys
    }
