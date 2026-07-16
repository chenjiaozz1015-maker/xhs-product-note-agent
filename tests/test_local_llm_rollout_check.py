from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from app.services import llm_content_service


def _load_module():
    path = Path("scripts/local_llm_rollout_check.py")
    spec = importlib.util.spec_from_file_location("local_llm_rollout_check", path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _status(ready: bool) -> llm_content_service.LLMConfigStatus:
    return llm_content_service.LLMConfigStatus(
        requested_engine_type="llm_openai_compatible",
        resolved_engine_type="llm_openai_compatible" if ready else "rule_based",
        llm_provider="openai_compatible",
        llm_config_ready=ready,
        status_code="llm_config_ready" if ready else "llm_config_missing",
        missing_fields=() if ready else ("LLM_API_KEY", "LLM_MODEL"),
        llm_base_url_status="configured" if ready else "missing",
        llm_model_status="configured" if ready else "missing",
        llm_api_key_status="configured" if ready else "missing",
        llm_api_key_preview="sk-****1234" if ready else "missing",
        llm_provider_source="app_settings",
        llm_base_url_source="app_settings",
        llm_model_source="app_settings",
        llm_api_key_source="app_settings",
    )


def test_incomplete_config_is_not_ready_and_does_not_request_llm(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module.llm_content_service, "get_llm_config_status", lambda *args, **kwargs: _status(False))
    monkeypatch.setattr(module, "_run_smoke", lambda *_: (_ for _ in ()).throw(AssertionError("must not request")))

    result = module.main(["--db", str(tmp_path / "missing.sqlite3")])

    output = capsys.readouterr().out
    assert result == 0
    assert "Final status: NOT_READY" in output
    assert "Missing: LLM_API_KEY, LLM_MODEL" in output


def test_ready_config_runs_steps_and_supports_skip_flags(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module.llm_content_service, "get_llm_config_status", lambda *args, **kwargs: _status(True))
    calls = []
    monkeypatch.setattr(module, "_run_smoke", lambda *_: calls.append("smoke") or {"status": "SUCCESS", "reason": ""})
    monkeypatch.setattr(module, "_run_compare", lambda *_: calls.append("compare") or {"status": "SUCCESS", "reason": ""})
    monkeypatch.setattr(module, "_run_batch", lambda: calls.append("batch") or {"status": "SUCCESS", "reason": ""})

    result = module.main(["--db", str(tmp_path / "missing.sqlite3"), "--skip-smoke"])

    output = capsys.readouterr().out
    assert result == 0
    assert calls == ["compare", "batch"]
    assert "Final status: READY_FOR_MANUAL_REVIEW" in output
    assert "LLM_API_KEY: configured via app_settings" in output


def test_json_output_is_safe_and_only_written_when_requested(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module.llm_content_service, "get_llm_config_status", lambda *args, **kwargs: _status(False))
    report_path = tmp_path / "local_llm_rollout_report.json"

    module.main(["--format", "json", "--output", str(report_path), "--db", str(tmp_path / "missing.sqlite3")])

    output = capsys.readouterr().out
    payload = json.loads(output)
    saved = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload == saved
    assert "sk-secret-key-1234" not in output
    assert "api_key_value" not in output
    assert payload["version"] == "v0.7-4"
