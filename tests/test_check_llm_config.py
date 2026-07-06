from __future__ import annotations

import importlib.util
from pathlib import Path

from app.services import llm_content_service


def _load_check_llm_config_module():
    script_path = Path("scripts/check_llm_config.py")
    spec = importlib.util.spec_from_file_location("check_llm_config", script_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_check_llm_config_masks_api_key(monkeypatch, capsys):
    monkeypatch.setattr(llm_content_service, "CONTENT_ENGINE_TYPE", "llm_openai_compatible")
    monkeypatch.setattr(llm_content_service, "LLM_PROVIDER", "openai_compatible")
    monkeypatch.setattr(llm_content_service, "LLM_API_KEY", "sk-secret-key-1234")
    monkeypatch.setattr(llm_content_service, "LLM_BASE_URL", "https://example.com/v1")
    monkeypatch.setattr(llm_content_service, "LLM_MODEL", "demo-model")
    monkeypatch.setattr(llm_content_service, "LLM_TIMEOUT_SECONDS_RAW", "15")
    monkeypatch.setattr(llm_content_service, "LLM_MAX_RETRIES_RAW", "1")

    module = _load_check_llm_config_module()
    exit_code = module.main()

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "LLM config looks ready" in captured
    assert "sk-secret-key-1234" not in captured
    assert "LLM_API_KEY preview:" in captured


def test_check_llm_config_reports_missing_fields(monkeypatch, capsys):
    monkeypatch.setattr(llm_content_service, "CONTENT_ENGINE_TYPE", "llm_openai_compatible")
    monkeypatch.setattr(llm_content_service, "LLM_PROVIDER", "openai_compatible")
    monkeypatch.setattr(llm_content_service, "LLM_API_KEY", "")
    monkeypatch.setattr(llm_content_service, "LLM_BASE_URL", "")
    monkeypatch.setattr(llm_content_service, "LLM_MODEL", "")
    monkeypatch.setattr(llm_content_service, "LLM_TIMEOUT_SECONDS_RAW", "15")
    monkeypatch.setattr(llm_content_service, "LLM_MAX_RETRIES_RAW", "1")

    module = _load_check_llm_config_module()
    module.main()

    captured = capsys.readouterr().out
    assert "LLM config incomplete, will fallback to rule_based" in captured
    assert "Missing: LLM_API_KEY, LLM_BASE_URL, LLM_MODEL" in captured
