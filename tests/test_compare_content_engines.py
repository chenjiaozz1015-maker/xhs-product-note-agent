from __future__ import annotations

import importlib.util
from pathlib import Path

from app.services import llm_content_service


def _load_compare_module():
    script_path = Path("scripts/compare_content_engines.py")
    spec = importlib.util.spec_from_file_location("compare_content_engines", script_path)
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


def _rule_note_data(product_name: str = "水牛奶蛋糕") -> dict[str, object]:
    return {
        "note_titles": [f"{product_name}值得回购", "早餐搭配很自然", "下午茶也顺口"],
        "note_body": f"{product_name}吃起来更偏日常分享风格，口感和场景都比较清楚。",
        "hashtags": ["#早餐友好", "#下午茶", "#家里囤"],
        "selling_points": ["口感松软", "搭配咖啡自然", "家里备着方便"],
    }


def _llm_note_data() -> dict[str, object]:
    return {
        "note_titles": ["这款真的适合早餐", "囤在家里很安心", "下午茶搭配也轻松"],
        "note_body": "整体更像真实体验分享，口感、场景和推荐理由会更集中一点。",
        "hashtags": ["#早餐", "#下午茶", "#真实测评"],
        "selling_points": ["口感更轻松", "分享感更自然", "标签更聚焦"],
    }


def test_compare_script_default_args_can_run(monkeypatch, capsys):
    module = _load_compare_module()
    monkeypatch.setattr(module, "generate_content_with_rule_based", lambda content_input: type("R", (), {"note_data": _rule_note_data(content_input.product_name)})())
    monkeypatch.setattr(module.llm_content_service, "get_llm_config_status", lambda *_: _incomplete_status())

    exit_code = module.main([])

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "Content Engine Compare" in captured
    assert "Product: 水牛奶蛋糕" in captured
    assert "Rule-based result:" in captured


def test_compare_script_skips_llm_when_config_incomplete(monkeypatch, capsys):
    module = _load_compare_module()
    request_called = False

    def fake_generate(*args, **kwargs):
        nonlocal request_called
        request_called = True
        raise AssertionError("LLM request should not be sent when config is incomplete")

    monkeypatch.setattr(module, "generate_content_with_rule_based", lambda content_input: type("R", (), {"note_data": _rule_note_data(content_input.product_name)})())
    monkeypatch.setattr(module.llm_content_service, "get_llm_config_status", lambda *_: _incomplete_status())
    monkeypatch.setattr(module.llm_content_service, "generate_openai_compatible_note_data", fake_generate)

    exit_code = module.main([])

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "Status: SKIPPED" in captured
    assert "Reason: LLM config incomplete" in captured
    assert "Missing: LLM_API_KEY, LLM_MODEL" in captured
    assert "No LLM request was sent." in captured
    assert request_called is False


def test_compare_script_prints_rule_and_llm_results_on_success(monkeypatch, capsys):
    module = _load_compare_module()
    monkeypatch.setattr(module, "generate_content_with_rule_based", lambda content_input: type("R", (), {"note_data": _rule_note_data(content_input.product_name)})())
    monkeypatch.setattr(module.llm_content_service, "get_llm_config_status", lambda *_: _ready_status())
    monkeypatch.setattr(
        module.llm_content_service,
        "generate_openai_compatible_note_data",
        lambda **_: llm_content_service.LLMContentResult(success=True, note_data=_llm_note_data()),
    )

    exit_code = module.main(["--product-name", "护手霜", "--category", "美妆护肤"])

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "Rule-based result:" in captured
    assert "LLM result:" in captured
    assert "Status: SUCCESS" in captured
    assert "LLM result detail:" in captured
    assert "sk-****1234" in captured
    assert "sk-secret-key-1234" not in captured


def test_compare_script_failed_llm_keeps_rule_based_result(monkeypatch, capsys):
    module = _load_compare_module()
    monkeypatch.setattr(module, "generate_content_with_rule_based", lambda content_input: type("R", (), {"note_data": _rule_note_data(content_input.product_name)})())
    monkeypatch.setattr(module.llm_content_service, "get_llm_config_status", lambda *_: _ready_status())
    monkeypatch.setattr(
        module.llm_content_service,
        "generate_openai_compatible_note_data",
        lambda **_: llm_content_service.LLMContentResult(success=False, error_message="llm_timeout"),
    )

    exit_code = module.main(["--product-name", "保温杯", "--category", "家居日用"])

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "Rule-based result:" in captured
    assert "Status: FAILED" in captured
    assert "Reason: llm_timeout" in captured
    assert "Rule-based result is still available." in captured
