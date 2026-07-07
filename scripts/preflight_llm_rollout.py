from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import CONTENT_ENGINE_TYPE, POSTER_ENGINE_TYPE
from app.services.llm_content_service import get_llm_config_status


def _status_label(status) -> str:
    if status.llm_config_ready:
        return "READY FOR MANUAL SMOKE CHECK"
    return "NOT READY"


def _next_steps(status) -> list[str]:
    if status.llm_config_ready:
        return [
            "Run python scripts/smoke_check_llm.py",
            "Run python scripts/compare_content_engines.py",
            "Run python scripts/batch_evaluate_content.py",
            "If results are acceptable, change CONTENT_ENGINE_TYPE to llm_openai_compatible in Render",
        ]
    return [
        "Configure LLM_API_KEY / LLM_BASE_URL / LLM_MODEL",
        "Run python scripts/check_llm_config.py",
        "Run python scripts/smoke_check_llm.py",
        "Run python scripts/batch_evaluate_content.py",
    ]


def main() -> int:
    status = get_llm_config_status("llm_openai_compatible")

    print("LLM Rollout Preflight\n")
    print(f"Current content engine: {CONTENT_ENGINE_TYPE}")
    print(f"Poster engine: {POSTER_ENGINE_TYPE}")
    print(f"LLM config ready: {str(status.llm_config_ready).lower()}")
    print(f"Provider: {status.llm_provider}")
    print(f"API key: {status.llm_api_key_status}")
    print(f"Base URL: {status.llm_base_url_status}")
    print(f"Model: {status.llm_model_status}")
    print(f"Timeout seconds: {status.timeout_seconds:g}")
    print(f"Max retries: {status.max_retries}")
    print(f"\nStatus: {_status_label(status)}")

    if status.missing_fields:
        print(f"Missing: {', '.join(status.missing_fields)}")
    if status.invalid_fields:
        print(f"Invalid: {', '.join(status.invalid_fields)}")

    print("Next steps:")
    for step in _next_steps(status):
        print(f"- {step}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
