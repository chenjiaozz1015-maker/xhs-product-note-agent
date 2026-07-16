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

    assert module.main(["--raw", "--dry-run", "--output", str(output)]) == 0
    raw_output = capsys.readouterr().out
    assert "raw=true" in raw_output
    assert "No request was sent." in raw_output

    assert module.main(["--output", str(output)]) == 1
    assert not output.exists()
    assert "runtime_token_file_missing" in capsys.readouterr().out


def test_secret_material_writes_json_env_content_without_printing_it(tmp_path, monkeypatch, capsys):
    module = _load_module()
    output = tmp_path / "secret.env"
    secret_content = "LLM_API_KEY=super-secret-value\n"
    monkeypatch.setattr(module, "load_runtime_config_token", lambda: {"available": True, "error": ""})
    monkeypatch.setattr(module, "fetch_secret_material", lambda **kwargs: {"available": True, "content": secret_content, "status_code": 200, "error": ""})

    assert module.main(["--output", str(output)]) == 0
    assert output.read_text(encoding="utf-8") == secret_content
    captured = capsys.readouterr().out
    assert "Secret keys found: LLM_API_KEY" in captured
    assert "super-secret-value" not in captured


def test_secret_material_rejects_empty_and_json_empty_payloads(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "load_runtime_config_token", lambda: {"available": True, "error": ""})

    for index, raw_content in enumerate(("", "{}", "null", "[]")):
        output = tmp_path / f"invalid-{index}.env"
        monkeypatch.setattr(
            module,
            "fetch_secret_material",
            lambda raw_content=raw_content, **kwargs: {
                "available": True,
                "content": raw_content,
                "status_code": 200,
                "error": "",
            },
        )

        assert module.main(["--output", str(output)]) == 1
        captured = capsys.readouterr().out
        assert "Secret material invalid: no env entries found" in captured
        if raw_content:
            assert raw_content not in captured
        assert not output.exists()


def test_secret_material_invalid_payload_does_not_overwrite_existing_file(tmp_path, monkeypatch, capsys):
    module = _load_module()
    output = tmp_path / "secret.env"
    output.write_text("LLM_API_KEY=old-value\n", encoding="utf-8")
    monkeypatch.setattr(module, "load_runtime_config_token", lambda: {"available": True, "error": ""})
    monkeypatch.setattr(
        module,
        "fetch_secret_material",
        lambda **kwargs: {"available": True, "content": "{}", "status_code": 200, "error": ""},
    )

    assert module.main(["--output", str(output), "--overwrite"]) == 1
    captured = capsys.readouterr().out

    assert "Secret material invalid: no env entries found" in captured
    assert output.read_text(encoding="utf-8") == "LLM_API_KEY=old-value\n"
    assert "old-value" not in captured


def test_secret_material_writes_export_env_content_without_printing_value(tmp_path, monkeypatch, capsys):
    module = _load_module()
    output = tmp_path / "secret.env"
    secret_content = 'export LLM_API_KEY="super-secret-value"\n'
    monkeypatch.setattr(module, "load_runtime_config_token", lambda: {"available": True, "error": ""})
    monkeypatch.setattr(
        module,
        "fetch_secret_material",
        lambda **kwargs: {"available": True, "content": secret_content, "status_code": 200, "error": ""},
    )

    assert module.main(["--output", str(output)]) == 0
    captured = capsys.readouterr().out

    assert output.read_text(encoding="utf-8") == secret_content
    assert "Secret keys found: LLM_API_KEY" in captured
    assert "super-secret-value" not in captured


def test_secret_material_extracts_json_wrapped_content(tmp_path, monkeypatch, capsys):
    module = _load_module()
    secret_content = "LLM_API_KEY=wrapped-secret-value\nLLM_MODEL=deepseek-chat\n"
    monkeypatch.setattr(module, "load_runtime_config_token", lambda: {"available": True, "error": ""})
    wrapped_payloads = [
        {"material": secret_content},
        {"env": secret_content},
        {"envContent": secret_content},
        {"content": secret_content},
        {"data": {"material": secret_content}},
        {"data": {"env": secret_content}},
        {"data": {"content": secret_content}},
    ]

    for index, payload in enumerate(wrapped_payloads):
        output = tmp_path / f"wrapped-{index}.env"
        monkeypatch.setattr(
            module,
            "fetch_secret_material",
            lambda payload=payload, **kwargs: {
                "available": True,
                "content": json.dumps(payload),
                "status_code": 200,
                "error": "",
            },
        )

        assert module.main(["--output", str(output)]) == 0
        captured = capsys.readouterr().out

        assert output.read_text(encoding="utf-8") == secret_content
        assert "Secret keys found: LLM_API_KEY" in captured
        assert "wrapped-secret-value" not in captured
        assert "deepseek-chat" not in captured


def test_secret_material_raw_mode_writes_plain_env_and_passes_raw_flag(tmp_path, monkeypatch, capsys):
    module = _load_module()
    output = tmp_path / "raw.env"
    secret_content = "LLM_API_KEY=raw-secret-value\n"
    captured_call = {}

    monkeypatch.setattr(module, "load_runtime_config_token", lambda: {"available": True, "error": ""})

    def fake_fetch_secret_material(*, raw=False):
        captured_call["raw"] = raw
        return {"available": True, "content": secret_content, "status_code": 200, "error": ""}

    monkeypatch.setattr(module, "fetch_secret_material", fake_fetch_secret_material)

    assert module.main(["--raw", "--output", str(output)]) == 0
    captured = capsys.readouterr().out

    assert captured_call["raw"] is True
    assert output.read_text(encoding="utf-8") == secret_content
    assert "Secret keys found: LLM_API_KEY" in captured
    assert "raw-secret-value" not in captured


def test_secret_material_raw_mode_rejects_invalid_plain_text(tmp_path, monkeypatch, capsys):
    module = _load_module()
    output = tmp_path / "raw-invalid.env"
    output.write_text("LLM_API_KEY=old-value\n", encoding="utf-8")
    captured_call = {}

    monkeypatch.setattr(module, "load_runtime_config_token", lambda: {"available": True, "error": ""})

    def fake_fetch_secret_material(*, raw=False):
        captured_call["raw"] = raw
        return {"available": True, "content": "not env content", "status_code": 200, "error": ""}

    monkeypatch.setattr(module, "fetch_secret_material", fake_fetch_secret_material)

    assert module.main(["--raw", "--overwrite", "--output", str(output)]) == 1
    captured = capsys.readouterr().out

    assert captured_call["raw"] is True
    assert "Secret material invalid: no env entries found" in captured
    assert "not env content" not in captured
    assert output.read_text(encoding="utf-8") == "LLM_API_KEY=old-value\n"


def test_existing_secret_material_requires_overwrite(tmp_path, monkeypatch, capsys):
    module = _load_module()
    output = tmp_path / "secret.env"
    output.write_text("old\n", encoding="utf-8")
    monkeypatch.setattr(module, "load_runtime_config_token", lambda: {"available": True, "error": ""})
    monkeypatch.setattr(module, "fetch_secret_material", lambda: (_ for _ in ()).throw(AssertionError("no request")))

    assert module.main(["--output", str(output)]) == 1
    assert output.read_text(encoding="utf-8") == "old\n"
    assert "--overwrite" in capsys.readouterr().out
