from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_module():
    path = Path("scripts/fetch_config_center_secret_material.py")
    spec = importlib.util.spec_from_file_location("fetch_secret_material", path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_missing_token_and_dry_run_do_not_request_or_write(tmp_path, monkeypatch, capsys):
    module = _load_module()
    output = tmp_path / "secret.env"
    monkeypatch.setattr(module, "load_runtime_config_token", lambda: {"available": False, "error": "runtime_token_file_missing"})
    monkeypatch.setattr(module, "fetch_secret_material", lambda: (_ for _ in ()).throw(AssertionError("no request")))

    assert module.main(["--dry-run", "--output", str(output)]) == 0
    assert not output.exists()
    assert "No request was sent." in capsys.readouterr().out

    assert module.main(["--output", str(output)]) == 1
    assert not output.exists()
    assert "runtime_token_file_missing" in capsys.readouterr().out


def test_secret_material_writes_json_env_content_without_printing_it(tmp_path, monkeypatch, capsys):
    module = _load_module()
    output = tmp_path / "secret.env"
    secret_content = "LLM_API_KEY=super-secret-value\n"
    monkeypatch.setattr(module, "load_runtime_config_token", lambda: {"available": True, "error": ""})
    monkeypatch.setattr(module, "fetch_secret_material", lambda: {"available": True, "content": secret_content, "status_code": 200, "error": ""})

    assert module.main(["--output", str(output)]) == 0
    assert output.read_text(encoding="utf-8") == secret_content
    assert "super-secret-value" not in capsys.readouterr().out


def test_existing_secret_material_requires_overwrite(tmp_path, monkeypatch, capsys):
    module = _load_module()
    output = tmp_path / "secret.env"
    output.write_text("old\n", encoding="utf-8")
    monkeypatch.setattr(module, "load_runtime_config_token", lambda: {"available": True, "error": ""})
    monkeypatch.setattr(module, "fetch_secret_material", lambda: (_ for _ in ()).throw(AssertionError("no request")))

    assert module.main(["--output", str(output)]) == 1
    assert output.read_text(encoding="utf-8") == "old\n"
    assert "--overwrite" in capsys.readouterr().out
