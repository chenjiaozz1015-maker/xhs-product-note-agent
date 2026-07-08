from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from urllib import error


def _load_module():
    script_path = Path("scripts/bootstrap_config_center.py")
    spec = importlib.util.spec_from_file_location("bootstrap_config_center", script_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


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


def test_default_run_requires_confirmation_and_does_not_request(monkeypatch, capsys, tmp_path):
    module = _load_module()
    called = {"value": False}
    token_file = tmp_path / "test.runtime-token.json"

    monkeypatch.setenv("CONFIG_CENTER_INVITE_CODE", "secret-invite-code")
    monkeypatch.setenv("CONFIG_CENTER_RUNTIME_TOKEN_FILE", str(token_file))
    monkeypatch.setattr(module, "_post_bootstrap", lambda *args, **kwargs: called.update(value=True))

    exit_code = module.main([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "This will bootstrap config-center project: zhongcaoji" in captured.out
    assert "Run again with --yes to confirm." in captured.out
    assert called["value"] is False
    assert not token_file.exists()


def test_dry_run_prints_summary_without_request(monkeypatch, capsys, tmp_path):
    module = _load_module()
    called = {"value": False}
    token_file = tmp_path / "test.runtime-token.json"

    monkeypatch.delenv("CONFIG_CENTER_INVITE_CODE", raising=False)
    monkeypatch.setenv("CONFIG_CENTER_RUNTIME_TOKEN_FILE", str(token_file))
    monkeypatch.setattr(module, "_post_bootstrap", lambda *args, **kwargs: called.update(value=True))

    exit_code = module.main(["--dry-run"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Config center bootstrap dry run" in captured.out
    assert "inviteCode: missing" in captured.out
    assert "No request was sent." in captured.out
    assert called["value"] is False
    assert not token_file.exists()


def test_invite_code_required_without_request(monkeypatch, capsys, tmp_path):
    module = _load_module()
    called = {"value": False}
    token_file = tmp_path / "test.runtime-token.json"

    monkeypatch.delenv("CONFIG_CENTER_INVITE_CODE", raising=False)
    monkeypatch.setenv("CONFIG_CENTER_RUNTIME_TOKEN_FILE", str(token_file))
    monkeypatch.setattr(module, "_post_bootstrap", lambda *args, **kwargs: called.update(value=True))

    exit_code = module.main(["--yes"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "CONFIG_CENTER_INVITE_CODE is required" in captured.out
    assert called["value"] is False
    assert not token_file.exists()


def test_builds_correct_default_payload_and_succeeds(monkeypatch, capsys, tmp_path):
    module = _load_module()
    captured_call: dict[str, object] = {}
    token_file = tmp_path / "test.runtime-token.json"

    monkeypatch.setenv("CONFIG_CENTER_INVITE_CODE", "secret-invite-code")
    monkeypatch.setenv("CONFIG_CENTER_RUNTIME_TOKEN_FILE", str(token_file))
    monkeypatch.delenv("CONFIG_CENTER_PROJECT_CODE", raising=False)
    monkeypatch.delenv("CONFIG_CENTER_RUNTIME", raising=False)
    monkeypatch.delenv("CONFIG_CENTER_BASE_URL", raising=False)
    monkeypatch.delenv("CONFIG_CENTER_LOCAL_WORKSPACE_ROOT", raising=False)

    def fake_post(base_url: str, payload: dict[str, str]):
        captured_call["base_url"] = base_url
        captured_call["payload"] = payload
        return 200, '{"runtimeConfigToken":"super-secret-runtime-token"}'

    monkeypatch.setattr(module, "_post_bootstrap", fake_post)

    exit_code = module.main(["--yes"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured_call["base_url"] == "http://39.106.61.160:28081"
    assert captured_call["payload"] == {
        "projectCode": "zhongcaoji",
        "runtime": "python",
        "inviteCode": "secret-invite-code",
        "localWorkspaceRoot": str(Path.cwd()),
    }
    assert "Config center bootstrap succeeded" in captured.out
    assert "projectCode: zhongcaoji" in captured.out
    assert "inviteCode: configured" in captured.out
    assert "secret-invite-code" not in captured.out
    assert "super-secret-runtime-token" not in captured.out
    assert token_file.exists()
    assert json.loads(token_file.read_text(encoding="utf-8")) == {
        "runtimeConfigToken": "super-secret-runtime-token"
    }


def test_bootstrap_writes_runtime_token_from_data_path(monkeypatch, tmp_path, capsys):
    module = _load_module()
    token_file = tmp_path / "nested-data.runtime-token.json"

    monkeypatch.setenv("CONFIG_CENTER_INVITE_CODE", "secret-invite-code")
    monkeypatch.setenv("CONFIG_CENTER_RUNTIME_TOKEN_FILE", str(token_file))
    monkeypatch.setattr(
        module,
        "_post_bootstrap",
        lambda *args, **kwargs: (200, '{"data":{"runtimeConfigToken":"secret-data-token"}}'),
    )

    exit_code = module.main(["--yes"])
    captured = capsys.readouterr().out

    assert exit_code == 0
    assert token_file.exists()
    assert json.loads(token_file.read_text(encoding="utf-8")) == {"runtimeConfigToken": "secret-data-token"}
    assert "secret-data-token" not in captured


def test_bootstrap_writes_runtime_token_from_result_path(monkeypatch, tmp_path):
    module = _load_module()
    token_file = tmp_path / "nested-result.runtime-token.json"

    monkeypatch.setenv("CONFIG_CENTER_INVITE_CODE", "secret-invite-code")
    monkeypatch.setenv("CONFIG_CENTER_RUNTIME_TOKEN_FILE", str(token_file))
    monkeypatch.setattr(
        module,
        "_post_bootstrap",
        lambda *args, **kwargs: (200, '{"result":{"runtimeConfigToken":"secret-result-token"}}'),
    )

    exit_code = module.main(["--yes"])

    assert exit_code == 0
    assert json.loads(token_file.read_text(encoding="utf-8")) == {"runtimeConfigToken": "secret-result-token"}


def test_bootstrap_writes_runtime_token_from_token_path(monkeypatch, tmp_path):
    module = _load_module()
    token_file = tmp_path / "nested-token.runtime-token.json"

    monkeypatch.setenv("CONFIG_CENTER_INVITE_CODE", "secret-invite-code")
    monkeypatch.setenv("CONFIG_CENTER_RUNTIME_TOKEN_FILE", str(token_file))
    monkeypatch.setattr(
        module,
        "_post_bootstrap",
        lambda *args, **kwargs: (200, '{"token":{"runtimeConfigToken":"secret-token-token"}}'),
    )

    exit_code = module.main(["--yes"])

    assert exit_code == 0
    assert json.loads(token_file.read_text(encoding="utf-8")) == {"runtimeConfigToken": "secret-token-token"}


def test_bootstrap_success_without_runtime_token_does_not_crash(monkeypatch, tmp_path, capsys):
    module = _load_module()
    token_file = tmp_path / "missing.runtime-token.json"

    monkeypatch.setenv("CONFIG_CENTER_INVITE_CODE", "secret-invite-code")
    monkeypatch.setenv("CONFIG_CENTER_RUNTIME_TOKEN_FILE", str(token_file))
    monkeypatch.setattr(module, "_post_bootstrap", lambda *args, **kwargs: (200, '{"ok":true,"data":{}}'))

    exit_code = module.main(["--yes"])
    captured = capsys.readouterr().out

    assert exit_code == 0
    assert "Config center bootstrap succeeded, but runtimeConfigToken was not found in response." in captured
    assert "Response keys: data, ok" in captured
    assert not token_file.exists()


def test_existing_token_file_is_not_overwritten_without_flag(monkeypatch, tmp_path, capsys):
    module = _load_module()
    token_file = tmp_path / "existing.runtime-token.json"
    token_file.write_text(json.dumps({"runtimeConfigToken": "old-token"}), encoding="utf-8")

    monkeypatch.setenv("CONFIG_CENTER_INVITE_CODE", "secret-invite-code")
    monkeypatch.setenv("CONFIG_CENTER_RUNTIME_TOKEN_FILE", str(token_file))
    monkeypatch.setattr(module, "_post_bootstrap", lambda *args, **kwargs: (200, '{"runtimeConfigToken":"new-token"}'))

    exit_code = module.main(["--yes"])
    captured = capsys.readouterr().out

    assert exit_code == 0
    assert "Runtime token file already exists. Use --overwrite-token to replace it." in captured
    assert json.loads(token_file.read_text(encoding="utf-8")) == {"runtimeConfigToken": "old-token"}


def test_existing_token_file_can_be_overwritten(monkeypatch, tmp_path, capsys):
    module = _load_module()
    token_file = tmp_path / "existing.runtime-token.json"
    token_file.write_text(json.dumps({"runtimeConfigToken": "old-token"}), encoding="utf-8")

    monkeypatch.setenv("CONFIG_CENTER_INVITE_CODE", "secret-invite-code")
    monkeypatch.setenv("CONFIG_CENTER_RUNTIME_TOKEN_FILE", str(token_file))
    monkeypatch.setattr(module, "_post_bootstrap", lambda *args, **kwargs: (200, '{"runtimeConfigToken":"new-token"}'))

    exit_code = module.main(["--yes", "--overwrite-token"])
    captured = capsys.readouterr().out

    assert exit_code == 0
    assert "Runtime token file written:" in captured
    assert json.loads(token_file.read_text(encoding="utf-8")) == {"runtimeConfigToken": "new-token"}


def test_failure_output_does_not_print_invite_code(monkeypatch, capsys, tmp_path):
    module = _load_module()
    token_file = tmp_path / "failed.runtime-token.json"

    monkeypatch.setenv("CONFIG_CENTER_INVITE_CODE", "secret-invite-code")
    monkeypatch.setenv("CONFIG_CENTER_RUNTIME_TOKEN_FILE", str(token_file))
    monkeypatch.setattr(module, "_post_bootstrap", lambda *args, **kwargs: (_ for _ in ()).throw(error.URLError("boom")))

    exit_code = module.main(["--yes"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Config center bootstrap failed" in captured.out
    assert "secret-invite-code" not in captured.out
    assert not token_file.exists()


def test_post_bootstrap_uses_expected_request_json(monkeypatch):
    module = _load_module()
    captured_request = {}

    def fake_urlopen(req, timeout=0):
        captured_request["url"] = req.full_url
        captured_request["method"] = req.get_method()
        captured_request["data"] = req.data.decode("utf-8")
        captured_request["headers"] = dict(req.header_items())
        captured_request["timeout"] = timeout
        return _FakeResponse(200, '{"ok":true}')

    monkeypatch.setattr(module.request, "urlopen", fake_urlopen)

    status_code, body = module._post_bootstrap(
        "http://39.106.61.160:28081",
        {
            "projectCode": "zhongcaoji",
            "runtime": "python",
            "inviteCode": "masked",
            "localWorkspaceRoot": "D:\\projects\\xhs-product-note-agent",
        },
    )

    assert status_code == 200
    assert json.loads(body) == {"ok": True}
    assert captured_request["url"] == "http://39.106.61.160:28081/internal/config-center/v1/projects/bootstrap"
    assert captured_request["method"] == "POST"
    assert json.loads(captured_request["data"])["projectCode"] == "zhongcaoji"
    assert captured_request["timeout"] == 15
