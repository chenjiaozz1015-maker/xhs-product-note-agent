from __future__ import annotations

from pathlib import Path


def test_config_center_integration_doc_exists_and_mentions_missing_read_api():
    doc_path = Path("docs/config_center_integration.md")
    assert doc_path.exists()

    content = doc_path.read_text(encoding="utf-8")
    assert "配置读取接口" in content
    assert "当前缺少配置读取接口" in content
    assert "CONFIG_CENTER_INVITE_CODE" in content
