from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from app.services import llm_content_service


def _load_batch_module():
    script_path = Path("scripts/batch_evaluate_content.py")
    spec = importlib.util.spec_from_file_location("batch_evaluate_content", script_path)
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


def _rule_note_data(product_name: str, category: str) -> dict[str, object]:
    return {
        "note_titles": [f"{product_name}值得一试", "标题二", "标题三"],
        "note_body": f"{product_name}在{category}场景下的规则文案结果。",
        "hashtags": ["#标签一", "#标签二", "#标签三"],
        "selling_points": ["卖点一", "卖点二", "卖点三"],
        "sub_category": "demo_sub_category",
    }


def _llm_note_data(product_name: str) -> dict[str, object]:
    return {
        "note_titles": [f"{product_name}的 LLM 标题", "LLM 标题二", "LLM 标题三"],
        "note_body": f"{product_name}的 LLM 文案结果。",
        "hashtags": ["#LLM一", "#LLM二", "#LLM三"],
        "selling_points": ["LLM 卖点一", "LLM 卖点二", "LLM 卖点三"],
        "sub_category": "demo_sub_category",
    }


def test_batch_script_default_args_can_run(monkeypatch, capsys):
    module = _load_batch_module()
    assert len(module.DEFAULT_SAMPLES) >= 6

    monkeypatch.setattr(
        module,
        "generate_content_with_rule_based",
        lambda content_input: type("R", (), {"note_data": _rule_note_data(content_input.product_name, content_input.category)})(),
    )
    monkeypatch.setattr(module.llm_content_service, "get_llm_config_status", lambda *_: _incomplete_status())

    exit_code = module.main([])

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "Batch Content Evaluation" in captured
    assert "Samples:" in captured
    assert "LLM: skipped" in captured


def test_batch_script_skips_llm_when_config_incomplete(monkeypatch, capsys):
    module = _load_batch_module()
    request_called = False

    def fake_generate(*args, **kwargs):
        nonlocal request_called
        request_called = True
        raise AssertionError("LLM request should not be sent when config is incomplete")

    monkeypatch.setattr(
        module,
        "generate_content_with_rule_based",
        lambda content_input: type("R", (), {"note_data": _rule_note_data(content_input.product_name, content_input.category)})(),
    )
    monkeypatch.setattr(module.llm_content_service, "get_llm_config_status", lambda *_: _incomplete_status())
    monkeypatch.setattr(module.llm_content_service, "generate_openai_compatible_note_data", fake_generate)

    exit_code = module.main([])

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "Status: SKIPPED" in captured
    assert "Missing: LLM_API_KEY, LLM_MODEL" in captured
    assert "No LLM requests were sent." in captured
    assert request_called is False


def test_batch_script_outputs_success_results(monkeypatch, capsys):
    module = _load_batch_module()
    monkeypatch.setattr(
        module,
        "generate_content_with_rule_based",
        lambda content_input: type("R", (), {"note_data": _rule_note_data(content_input.product_name, content_input.category)})(),
    )
    monkeypatch.setattr(module.llm_content_service, "get_llm_config_status", lambda *_: _ready_status())
    monkeypatch.setattr(
        module.llm_content_service,
        "generate_openai_compatible_note_data",
        lambda *, content_input, fallback_note_data: llm_content_service.LLMContentResult(
            success=True,
            note_data=_llm_note_data(content_input.product_name),
        ),
    )

    exit_code = module.main(["--format", "json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["llm_status"] == "ready"
    assert all(sample["llm"]["status"] == "SUCCESS" for sample in payload["samples"])


def test_batch_script_failed_sample_does_not_stop_following_samples(monkeypatch, capsys):
    module = _load_batch_module()
    call_count = {"value": 0}

    monkeypatch.setattr(
        module,
        "generate_content_with_rule_based",
        lambda content_input: type("R", (), {"note_data": _rule_note_data(content_input.product_name, content_input.category)})(),
    )
    monkeypatch.setattr(module.llm_content_service, "get_llm_config_status", lambda *_: _ready_status())

    def fake_generate(*, content_input, fallback_note_data):
        call_count["value"] += 1
        if call_count["value"] == 3:
            return llm_content_service.LLMContentResult(success=False, error_message="llm_timeout")
        return llm_content_service.LLMContentResult(success=True, note_data=_llm_note_data(content_input.product_name))

    monkeypatch.setattr(module.llm_content_service, "generate_openai_compatible_note_data", fake_generate)

    exit_code = module.main(["--format", "json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["samples"][2]["llm"]["status"] == "FAILED"
    assert payload["samples"][3]["llm"]["status"] == "SUCCESS"


def test_batch_script_writes_markdown_and_json_without_full_api_key(monkeypatch, tmp_path):
    module = _load_batch_module()
    monkeypatch.setattr(
        module,
        "generate_content_with_rule_based",
        lambda content_input: type("R", (), {"note_data": _rule_note_data(content_input.product_name, content_input.category)})(),
    )
    monkeypatch.setattr(module.llm_content_service, "get_llm_config_status", lambda *_: _ready_status())
    monkeypatch.setattr(
        module.llm_content_service,
        "generate_openai_compatible_note_data",
        lambda *, content_input, fallback_note_data: llm_content_service.LLMContentResult(
            success=True,
            note_data=_llm_note_data(content_input.product_name),
        ),
    )

    md_path = tmp_path / "content_eval.md"
    json_path = tmp_path / "content_eval.json"

    assert module.main(["--format", "markdown", "--output", str(md_path)]) == 0
    assert module.main(["--format", "json", "--output", str(json_path)]) == 0

    md_content = md_path.read_text(encoding="utf-8")
    json_content = json_path.read_text(encoding="utf-8")
    assert "sk-secret-key-1234" not in md_content
    assert "sk-secret-key-1234" not in json_content
    assert "sk-****1234" not in md_content
    assert "sk-****1234" not in json_content
