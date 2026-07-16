from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    script_path = Path("scripts/list_ops_tools.py")
    spec = importlib.util.spec_from_file_location("list_ops_tools", script_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_list_ops_tools_can_run_and_print_all_scripts(capsys):
    module = _load_module()

    exit_code = module.main()
    captured = capsys.readouterr().out

    assert exit_code == 0
    assert "Zhongcaoji Ops Tools" in captured
    assert "manage_user_plan.py" in captured
    assert "reset_user_password.py" in captured
    assert "check_llm_config.py" in captured
    assert "preflight_llm_rollout.py" in captured
    assert "smoke_check_llm.py" in captured
    assert "compare_content_engines.py" in captured
    assert "batch_evaluate_content.py" in captured
    assert "local_llm_rollout_check.py" in captured
    assert "engine_usage_report.py" in captured
    assert "bootstrap_config_center.py" in captured
    assert "check_config_center_runtime.py" in captured
    assert "fetch_config_center_secret_material.py" in captured
    assert "settings_set.py" in captured
    assert "settings_get.py" in captured
    assert "settings_list.py" in captured
    assert "docs/config_center_integration.md" in captured
    assert "scripts/README.md" in captured
    assert "docs/llm_rollout_runbook.md" in captured


def test_scripts_readme_exists_and_documents_boundaries():
    readme_path = Path("scripts/README.md")
    assert readme_path.exists()

    content = readme_path.read_text(encoding="utf-8")
    for expected in [
        "smoke_check_llm.py",
        "compare_content_engines.py",
        "batch_evaluate_content.py",
        "bootstrap_config_center.py",
        "check_config_center_runtime.py",
        "reset_user_password.py",
        "是否请求外网",
        "是否修改数据库",
        "LLM 启用前检查",
        "LLM 启用后观察",
        "配置中心初始化",
        "配置中心 runtime-config 读取",
        "--overwrite-token",
        "CONTENT_ENGINE_TYPE=rule_based",
        "settings_set.py",
        "settings_get.py",
        "settings_list.py",
        "local_llm_rollout_check.py",
        "fetch_config_center_secret_material.py",
    ]:
        assert expected in content


def test_project_readme_includes_ops_tool_entry():
    readme_path = Path("README.md")
    content = readme_path.read_text(encoding="utf-8")

    assert "python scripts/list_ops_tools.py" in content
    assert 'python scripts/reset_user_password.py --email user@example.com --password "NewPassword123"' in content
    assert "python scripts/bootstrap_config_center.py --dry-run" in content
    assert "python scripts/check_config_center_runtime.py" in content
    assert "scripts/README.md" in content
    assert "docs/llm_rollout_runbook.md" in content
    assert "docs/config_center_integration.md" in content
