from __future__ import annotations


def main() -> int:
    print(
        """Zhongcaoji Ops Tools

User / Plan:

manage_user_plan.py
show user: python scripts/manage_user_plan.py show --email user@example.com
set plan: python scripts/manage_user_plan.py set-plan --email user@example.com --plan personal
list users: python scripts/manage_user_plan.py list --limit 20

LLM rollout:

preflight_llm_rollout.py
check_llm_config.py
smoke_check_llm.py

Content evaluation:

compare_content_engines.py
batch_evaluate_content.py

Monitoring:

engine_usage_report.py

Config center:

bootstrap_config_center.py
dry run: python scripts/bootstrap_config_center.py --dry-run
bootstrap: python scripts/bootstrap_config_center.py --yes
check_config_center_runtime.py
runtime check: python scripts/check_config_center_runtime.py

Docs:

scripts/README.md
docs/llm_rollout_runbook.md
docs/config_center_integration.md
"""
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
