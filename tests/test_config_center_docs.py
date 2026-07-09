from __future__ import annotations

from pathlib import Path


def test_config_center_integration_doc_exists_and_mentions_runtime_config():
    doc_path = Path("docs/config_center_integration.md")
    assert doc_path.exists()

    content = doc_path.read_text(encoding="utf-8")
    assert "runtime-config" in content
    assert "重新按新版 bootstrap 流程执行" in content
    assert ".config-center/test.runtime-token.json" in content
    assert "X-Project-Config-Token" in content
    assert "inviteCode" in content
    assert "--overwrite-token" in content


def test_gitignore_includes_runtime_token_patterns():
    content = Path(".gitignore").read_text(encoding="utf-8")

    assert ".config-center/*.runtime-token.json" in content
    assert ".config-center/*.token.json" in content
    assert ".tmp/" in content
    assert ".pytest_cache/" in content
