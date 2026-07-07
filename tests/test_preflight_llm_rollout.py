from __future__ import annotations

import importlib.util
from pathlib import Path

from app.services import llm_content_service


def _load_preflight_module():
    script_path = Path("scripts/preflight_llm_rollout.py")
    spec = importlib.util.spec_from_file_location("preflight_llm_rollout", script_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _ready_status() -> llm_content_service.LLMConfigStatus:
    return llm_content_service.LLMConfigStatus(
        requested_engine_type="llm_openai_compatible",
        resolved_engine_type="llm_openai_compatible",
        llm_provider="openai_compatible",
        llm_config_ready=True,
        status_code="llm_config_ready",
        llm_base_url_status="configured",
        llm_model_status="configured",
        llm_api_key_status="configured",
        llm_api_key_preview="sk-****1234",
        timeout_seconds=15.0,
        max_retries=1,
    )


def _incomplete_status() -> llm_content_service.LLMConfigStatus:
    return llm_content_service.LLMConfigStatus(
        requested_engine_type="llm_openai_compatible",
        resolved_engine_type="rule_based",
        llm_provider="openai_compatible",
        llm_config_ready=False,
        status_code="llm_config_missing",
        missing_fields=("LLM_API_KEY", "LLM_MODEL"),
        llm_base_url_status="configured",
        llm_model_status="missing",
        llm_api_key_status="missing",
        llm_api_key_preview="missing",
        timeout_seconds=15.0,
        max_retries=1,
    )


def test_preflight_not_ready_when_config_incomplete(monkeypatch, capsys):
    module = _load_preflight_module()
    monkeypatch.setattr(module, "CONTENT_ENGINE_TYPE", "rule_based")
    monkeypatch.setattr(module, "POSTER_ENGINE_TYPE", "pillow")
    monkeypatch.setattr(module, "get_llm_config_status", lambda *_: _incomplete_status())

    exit_code = module.main()

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "LLM Rollout Preflight" in captured
    assert "Current content engine: rule_based" in captured
    assert "Status: NOT READY" in captured
    assert "Missing: LLM_API_KEY, LLM_MODEL" in captured
    assert "Run python scripts/check_llm_config.py" in captured


def test_preflight_ready_for_manual_smoke_check(monkeypatch, capsys):
    module = _load_preflight_module()
    monkeypatch.setattr(module, "CONTENT_ENGINE_TYPE", "rule_based")
    monkeypatch.setattr(module, "POSTER_ENGINE_TYPE", "pillow")
    monkeypatch.setattr(module, "get_llm_config_status", lambda *_: _ready_status())

    exit_code = module.main()

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "Status: READY FOR MANUAL SMOKE CHECK" in captured
    assert "Run python scripts/smoke_check_llm.py" in captured
    assert "If results are acceptable, change CONTENT_ENGINE_TYPE to llm_openai_compatible in Render" in captured
    assert "sk-secret-key-1234" not in captured


def test_runbook_exists_and_includes_rollback_steps():
    runbook = Path("docs/llm_rollout_runbook.md")
    assert runbook.exists()
    content = runbook.read_text(encoding="utf-8")
    assert "CONTENT_ENGINE_TYPE=rule_based" in content
    assert "python scripts/check_llm_config.py" in content
    assert "python scripts/smoke_check_llm.py" in content
    assert "python scripts/compare_content_engines.py" in content
    assert "python scripts/batch_evaluate_content.py" in content
    assert "快速回退方式" in content
