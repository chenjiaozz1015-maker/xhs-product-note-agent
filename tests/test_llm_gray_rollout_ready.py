from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sqlite3
from urllib import request


def _load_module():
    path = Path("scripts/llm_gray_rollout_ready.py")
    spec = importlib.util.spec_from_file_location("llm_gray_rollout_ready", path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _create_settings_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE app_settings (key TEXT PRIMARY KEY, value TEXT, is_secret INTEGER DEFAULT 0)"
        )
        connection.execute(
            "CREATE TABLE generation_records (id INTEGER PRIMARY KEY, product_name TEXT)"
        )
        connection.execute("INSERT INTO generation_records (product_name) VALUES ('demo')")
        connection.commit()


def _prepare_ready_root(module, tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setattr(module, "ROOT_DIR", tmp_path)
    secret_file = tmp_path / ".config-center" / "test.secret-material.env"
    monkeypatch.setattr(module, "DEFAULT_SECRET_MATERIAL_FILE", secret_file)
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "docs" / "llm_gray_rollout_runbook.md").write_text("runbook", encoding="utf-8")
    (tmp_path / "scripts").mkdir(parents=True)
    (tmp_path / "scripts" / "engine_usage_report.py").write_text("# observation\n", encoding="utf-8")
    (tmp_path / "local_llm_rollout_report.json").write_text(
        json.dumps({"steps": {"smoke_check": {"status": "SUCCESS"}}}),
        encoding="utf-8",
    )
    secret_file.parent.mkdir(parents=True)
    secret_file.write_text("LLM_API_KEY=dummy\n", encoding="utf-8")
    runtime_token_file = tmp_path / ".config-center" / "test.runtime-token.json"
    runtime_token_file.write_text(json.dumps({"runtimeConfigToken": "dummy"}), encoding="utf-8")
    monkeypatch.setenv("CONFIG_CENTER_RUNTIME_TOKEN_FILE", str(runtime_token_file))
    monkeypatch.setenv("LLM_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("LLM_MODEL", "demo-model")
    monkeypatch.setenv("LLM_API_KEY", "super-secret-value")
    db_path = tmp_path / "ready.sqlite3"
    _create_settings_db(db_path)
    return db_path


def test_llm_gray_rollout_runbook_exists_and_contains_switch_and_rollback():
    runbook = Path("docs/llm_gray_rollout_runbook.md")
    assert runbook.exists()
    content = runbook.read_text(encoding="utf-8")
    assert "CONTENT_ENGINE_TYPE=llm_openai_compatible" in content
    assert "CONTENT_ENGINE_TYPE=rule_based" in content
    assert "快速回退" in content


def test_llm_gray_rollout_ready_outputs_ready(monkeypatch, tmp_path, capsys):
    module = _load_module()
    db_path = _prepare_ready_root(module, tmp_path, monkeypatch)

    assert module.main(["--db", str(db_path)]) == 0
    output = capsys.readouterr().out

    assert "Recommendation: READY_FOR_MANUAL_DECISION" in output
    assert "LLM config: READY" in output
    assert "super-secret-value" not in output


def test_llm_gray_rollout_ready_outputs_not_ready(monkeypatch, tmp_path, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(module, "DEFAULT_SECRET_MATERIAL_FILE", tmp_path / ".config-center" / "missing.env")
    db_path = tmp_path / "missing.sqlite3"

    assert module.main(["--db", str(db_path)]) == 0
    output = capsys.readouterr().out

    assert "Recommendation: NOT_READY" in output
    assert "LLM_API_KEY" in output
    assert "local rollout smoke success not confirmed" in output


def test_llm_gray_rollout_ready_json_output_and_report_file_are_safe(monkeypatch, tmp_path, capsys):
    module = _load_module()
    db_path = _prepare_ready_root(module, tmp_path, monkeypatch)
    output_path = tmp_path / "llm_gray_rollout_ready.json"

    assert module.main(["--json", "--output", str(output_path), "--db", str(db_path)]) == 0
    stdout = capsys.readouterr().out
    payload = json.loads(stdout)
    saved_payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["recommendation"] == "READY_FOR_MANUAL_DECISION"
    assert saved_payload["recommendation"] == "READY_FOR_MANUAL_DECISION"
    assert "super-secret-value" not in stdout
    assert "super-secret-value" not in output_path.read_text(encoding="utf-8")
    assert payload["llm_api_key"] == "configured"


def test_llm_gray_rollout_ready_default_does_not_write_file(monkeypatch, tmp_path):
    module = _load_module()
    db_path = _prepare_ready_root(module, tmp_path, monkeypatch)
    expected_output = Path("llm_gray_rollout_ready.json")
    if expected_output.exists():
        expected_output.unlink()

    assert module.main(["--db", str(db_path)]) == 0
    assert not expected_output.exists()


def test_llm_gray_rollout_ready_is_read_only_and_does_not_request_network(monkeypatch, tmp_path):
    module = _load_module()
    db_path = _prepare_ready_root(module, tmp_path, monkeypatch)
    before = db_path.read_bytes()
    monkeypatch.setattr(
        request,
        "urlopen",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no network")),
    )

    assert module.main(["--json", "--db", str(db_path)]) == 0
    assert db_path.read_bytes() == before
