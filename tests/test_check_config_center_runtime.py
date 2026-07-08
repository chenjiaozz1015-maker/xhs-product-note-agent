from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    script_path = Path("scripts/check_config_center_runtime.py")
    spec = importlib.util.spec_from_file_location("check_config_center_runtime", script_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_runtime_check_reports_not_ready_without_token(monkeypatch, capsys):
    module = _load_module()

    monkeypatch.setattr(
        module,
        "get_config_center_settings",
        lambda: {
            "project_code": "zhongcaoji",
            "env": "test",
            "runtime_token_file": ".config-center/test.runtime-token.json",
        },
    )
    monkeypatch.setattr(
        module,
        "load_runtime_config_token",
        lambda: {
            "available": False,
            "error": "runtime_token_file_missing",
        },
    )

    exit_code = module.main()
    captured = capsys.readouterr().out

    assert exit_code == 1
    assert "Status: NOT READY" in captured
    assert "Reason: runtime_token_file_missing" in captured


def test_runtime_check_reports_ready_with_only_config_keys(monkeypatch, capsys):
    module = _load_module()

    monkeypatch.setattr(
        module,
        "get_config_center_settings",
        lambda: {
            "project_code": "zhongcaoji",
            "env": "test",
            "runtime_token_file": ".config-center/test.runtime-token.json",
        },
    )
    monkeypatch.setattr(
        module,
        "load_runtime_config_token",
        lambda: {
            "available": True,
            "token": "super-secret-runtime-token",
        },
    )
    monkeypatch.setattr(
        module,
        "fetch_project_config",
        lambda: {
            "available": True,
            "status_code": 200,
            "config": {"key1": "value1", "key2": "value2"},
            "error": "",
        },
    )

    exit_code = module.main()
    captured = capsys.readouterr().out

    assert exit_code == 0
    assert "Status: READY" in captured
    assert "HTTP status: 200" in captured
    assert "Config keys: key1, key2" in captured
    assert "super-secret-runtime-token" not in captured
    assert "value1" not in captured


def test_runtime_check_reports_failed_request(monkeypatch, capsys):
    module = _load_module()

    monkeypatch.setattr(
        module,
        "get_config_center_settings",
        lambda: {
            "project_code": "zhongcaoji",
            "env": "test",
            "runtime_token_file": ".config-center/test.runtime-token.json",
        },
    )
    monkeypatch.setattr(
        module,
        "load_runtime_config_token",
        lambda: {
            "available": True,
            "token": "super-secret-runtime-token",
        },
    )
    monkeypatch.setattr(
        module,
        "fetch_project_config",
        lambda: {
            "available": False,
            "status_code": 401,
            "config": {},
            "error": "runtime_config_http_error",
        },
    )

    exit_code = module.main()
    captured = capsys.readouterr().out

    assert exit_code == 1
    assert "Status: FAILED" in captured
    assert "Reason: runtime_config_http_error" in captured
    assert "HTTP status: 401" in captured
