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
    assert "check_llm_config.py" in captured
    assert "preflight_llm_rollout.py" in captured
    assert "smoke_check_llm.py" in captured
    assert "compare_content_engines.py" in captured
    assert "batch_evaluate_content.py" in captured
    assert "engine_usage_report.py" in captured
    assert "scripts/README.md" in captured
    assert "docs/llm_rollout_runbook.md" in captured


def test_scripts_readme_exists_and_documents_boundaries():
    readme_path = Path("scripts/README.md")
    assert readme_path.exists()

    content = readme_path.read_text(encoding="utf-8")
    assert "smoke_check_llm.py" in content
    assert "compare_content_engines.py" in content
    assert "batch_evaluate_content.py" in content
    assert "是否请求外网" in content
    assert "是否修改数据库" in content
    assert "LLM 启用前检查" in content
    assert "LLM 启用后观察" in content
    assert "CONTENT_ENGINE_TYPE=rule_based" in content


def test_project_readme_includes_ops_tool_entry():
    readme_path = Path("README.md")
    content = readme_path.read_text(encoding="utf-8")

    assert "python scripts/list_ops_tools.py" in content
    assert "scripts/README.md" in content
    assert "docs/llm_rollout_runbook.md" in content
