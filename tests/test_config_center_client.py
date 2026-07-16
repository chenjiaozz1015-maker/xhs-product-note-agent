from __future__ import annotations

import json
from pathlib import Path
from urllib import error

from app.services import config_center_client


class _FakeResponse:
    def __init__(self, status_code: int, body: str = "{}") -> None:
        self._status_code = status_code
        self._body = body.encode("utf-8")

    def getcode(self) -> int:
        return self._status_code

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def _write_token_file(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_get_config_center_settings_uses_runtime_defaults(monkeypatch, tmp_path):
    token_path = tmp_path / "runtime" / "test.runtime-token.json"
    monkeypatch.setenv("CONFIG_CENTER_RUNTIME_TOKEN_FILE", str(token_path))
    monkeypatch.setenv("CONFIG_CENTER_ENV", "test")
    monkeypatch.setenv("CONFIG_CENTER_TIMEOUT_SECONDS", "12")

    settings = config_center_client.get_config_center_settings()

    assert settings["project_code"] == "zhongcaoji"
    assert settings["env"] == "test"
    assert settings["timeout_seconds"] == 12.0
    resolved_runtime_token_file = Path(settings["runtime_token_file"])
    if not resolved_runtime_token_file.is_absolute():
        resolved_runtime_token_file = (config_center_client.BASE_DIR / resolved_runtime_token_file).resolve()
    assert resolved_runtime_token_file == token_path.resolve()


def test_load_runtime_config_token_missing_file(monkeypatch, tmp_path):
    token_path = tmp_path / "missing.runtime-token.json"
    monkeypatch.setenv("CONFIG_CENTER_RUNTIME_TOKEN_FILE", str(token_path))

    result = config_center_client.load_runtime_config_token()

    assert result["available"] is False
    assert result["error"] == "runtime_token_file_missing"


def test_load_runtime_config_token_invalid_json(monkeypatch, tmp_path):
    token_path = tmp_path / "bad.runtime-token.json"
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text("{bad json", encoding="utf-8")
    monkeypatch.setenv("CONFIG_CENTER_RUNTIME_TOKEN_FILE", str(token_path))

    result = config_center_client.load_runtime_config_token()

    assert result["available"] is False
    assert result["error"] == "runtime_token_invalid_json"


def test_load_runtime_config_token_missing_field(monkeypatch, tmp_path):
    token_path = tmp_path / "empty.runtime-token.json"
    _write_token_file(token_path, {"hello": "world"})
    monkeypatch.setenv("CONFIG_CENTER_RUNTIME_TOKEN_FILE", str(token_path))

    result = config_center_client.load_runtime_config_token()

    assert result["available"] is False
    assert result["error"] == "runtime_token_missing"


def test_fetch_project_config_success_uses_expected_url_and_header(monkeypatch, tmp_path):
    token_path = tmp_path / "ok.runtime-token.json"
    _write_token_file(token_path, {"runtimeConfigToken": "super-secret-runtime-token"})
    monkeypatch.setenv("CONFIG_CENTER_RUNTIME_TOKEN_FILE", str(token_path))
    monkeypatch.setenv("CONFIG_CENTER_BASE_URL", "http://39.106.61.160:28081")
    monkeypatch.setenv("CONFIG_CENTER_PROJECT_CODE", "zhongcaoji")
    monkeypatch.setenv("CONFIG_CENTER_ENV", "test")
    monkeypatch.setenv("CONFIG_CENTER_TIMEOUT_SECONDS", "10")

    captured = {}

    def fake_urlopen(req, timeout=0):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.header_items())
        captured["method"] = req.get_method()
        captured["timeout"] = timeout
        return _FakeResponse(200, '{"key1":"value1","key2":"value2"}')

    monkeypatch.setattr(config_center_client.request, "urlopen", fake_urlopen)

    result = config_center_client.fetch_project_config()

    assert result["available"] is True
    assert result["status_code"] == 200
    assert result["config"] == {"key1": "value1", "key2": "value2"}
    assert result["error"] == ""
    assert "token" not in result
    assert captured["url"] == "http://39.106.61.160:28081/internal/config-center/v1/projects/zhongcaoji/runtime-config?env=test&clientVersion=v0.7-4"
    assert captured["headers"]["X-project-config-token"] == "super-secret-runtime-token"
    assert captured["method"] == "GET"
    assert captured["timeout"] == 10.0


def test_fetch_project_config_extracts_llm_yaml(monkeypatch, tmp_path):
    token_path = tmp_path / "ok.runtime-token.json"
    _write_token_file(token_path, {"runtimeConfigToken": "secret-token"})
    monkeypatch.setenv("CONFIG_CENTER_RUNTIME_TOKEN_FILE", str(token_path))
    monkeypatch.setattr(
        config_center_client.request,
        "urlopen",
        lambda req, timeout=0: _FakeResponse(200, json.dumps({"files": {"llm.yaml": "LLM_PROVIDER=deepseek\n"}})),
    )

    result = config_center_client.fetch_project_config()

    assert result["llm_yaml_found"] is True
    assert result["llm_settings"] == {"LLM_PROVIDER": "deepseek"}


def test_fetch_project_config_http_error(monkeypatch, tmp_path):
    token_path = tmp_path / "ok.runtime-token.json"
    _write_token_file(token_path, {"runtimeConfigToken": "secret-token"})
    monkeypatch.setenv("CONFIG_CENTER_RUNTIME_TOKEN_FILE", str(token_path))

    def fake_urlopen(req, timeout=0):
        raise error.HTTPError(req.full_url, 401, "unauthorized", hdrs=None, fp=None)

    monkeypatch.setattr(config_center_client.request, "urlopen", fake_urlopen)

    result = config_center_client.fetch_project_config()

    assert result["available"] is False
    assert result["status_code"] == 401
    assert result["error"] == "runtime_config_http_error"


def test_fetch_project_config_invalid_json(monkeypatch, tmp_path):
    token_path = tmp_path / "ok.runtime-token.json"
    _write_token_file(token_path, {"runtimeConfigToken": "secret-token"})
    monkeypatch.setenv("CONFIG_CENTER_RUNTIME_TOKEN_FILE", str(token_path))

    monkeypatch.setattr(
        config_center_client.request,
        "urlopen",
        lambda req, timeout=0: _FakeResponse(200, "not-json"),
    )

    result = config_center_client.fetch_project_config()

    assert result["available"] is False
    assert result["status_code"] == 200
    assert result["error"] == "runtime_config_invalid_json"


def test_fetch_project_config_request_failure(monkeypatch, tmp_path):
    token_path = tmp_path / "ok.runtime-token.json"
    _write_token_file(token_path, {"runtimeConfigToken": "secret-token"})
    monkeypatch.setenv("CONFIG_CENTER_RUNTIME_TOKEN_FILE", str(token_path))

    monkeypatch.setattr(
        config_center_client.request,
        "urlopen",
        lambda req, timeout=0: (_ for _ in ()).throw(error.URLError("boom")),
    )

    result = config_center_client.fetch_project_config()

    assert result["available"] is False
    assert result["status_code"] is None
    assert result["error"] == "runtime_config_request_failed"
