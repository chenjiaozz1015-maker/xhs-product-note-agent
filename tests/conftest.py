from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from app.services import settings_service


LLM_RUNTIME_ENV_KEYS = (
    "LLM_PROVIDER",
    "LLM_BASE_URL",
    "LLM_MODEL",
    "LLM_API_KEY",
    "LLM_TIMEOUT_SECONDS",
    "LLM_MAX_RETRIES",
    "CONTENT_ENGINE_TYPE",
)


@pytest.fixture(autouse=True)
def isolate_llm_runtime_config(monkeypatch):
    for key in LLM_RUNTIME_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    runtime_dir = Path(".tmp") / "pytest-runtime-settings" / uuid4().hex
    runtime_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(settings_service, "DATABASE_PATH", runtime_dir / "app_settings.sqlite3")
    yield
    shutil.rmtree(runtime_dir, ignore_errors=True)
