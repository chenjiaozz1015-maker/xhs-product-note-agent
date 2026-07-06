from __future__ import annotations

import importlib.util
from pathlib import Path

from app.services import llm_content_service


def _load_smoke_check_module():
    script_path = Path("scripts/smoke_check_llm.py")
    spec = importlib.util.spec_from_file_location("smoke_check_llm", script_path)
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
        max_retries=0,
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
        max_retries=0,
    )


def test_smoke_check_skips_when_config_incomplete(monkeypatch, capsys):
    module = _load_smoke_check_module()
    request_called = False

    def fake_generate(*args, **kwargs):
        nonlocal request_called
        request_called = True
        raise AssertionError("LLM request should not be sent when config is incomplete")

    monkeypatch.setattr(module.llm_content_service, "get_llm_config_status", lambda *_: _incomplete_status())
    monkeypatch.setattr(module.llm_content_service, "generate_openai_compatible_note_data", fake_generate)

    exit_code = module.main([])

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "Status: SKIPPED" in captured
    assert "Reason: LLM config incomplete" in captured
    assert "Missing: LLM_API_KEY, LLM_MODEL" in captured
    assert "No request was sent." in captured
    assert request_called is False


def test_smoke_check_success_prints_summary_and_masks_api_key(monkeypatch, capsys):
    module = _load_smoke_check_module()

    monkeypatch.setattr(module.llm_content_service, "get_llm_config_status", lambda *_: _ready_status())
    monkeypatch.setattr(
        module.llm_content_service,
        "generate_openai_compatible_note_data",
        lambda **_: llm_content_service.LLMContentResult(
            success=True,
            note_data={
                "note_titles": ["早餐党真的会囤", "下午茶也很搭", "家里备着很安心"],
                "note_body": "这类点心拿来配咖啡和牛奶都很自然，早上和下午茶都顺口。",
                "hashtags": ["#早餐友好", "#下午茶", "#家里囤"],
                "selling_points": ["口感松软", "配茶刚好", "家里备一点更省心"],
            },
        ),
    )

    exit_code = module.main([])

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "Status: SUCCESS" in captured
    assert "Generated titles:" in captured
    assert "Body preview:" in captured
    assert "Hashtags:" in captured
    assert "Selling points:" in captured
    assert "sk-****1234" in captured
    assert "sk-secret-key-1234" not in captured


def test_smoke_check_failed_request_reports_reason(monkeypatch, capsys):
    module = _load_smoke_check_module()

    monkeypatch.setattr(module.llm_content_service, "get_llm_config_status", lambda *_: _ready_status())
    monkeypatch.setattr(
        module.llm_content_service,
        "generate_openai_compatible_note_data",
        lambda **_: llm_content_service.LLMContentResult(
            success=False,
            error_message="llm_timeout",
        ),
    )

    exit_code = module.main(["--product-name", "护手霜", "--category", "美妆护肤"])

    captured = capsys.readouterr().out
    assert exit_code == 1
    assert "Status: FAILED" in captured
    assert "Reason: llm_timeout" in captured
    assert "Fallback: rule_based is still available for normal generation" in captured
