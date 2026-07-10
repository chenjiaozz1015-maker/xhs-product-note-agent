from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services.llm_content_service import get_llm_config_status
from app.services.runtime_config_service import get_runtime_config_value


def _status_text(status_code: str) -> str:
    if status_code == "llm_config_ready":
        return "LLM config looks ready"
    if status_code == "llm_disabled":
        return "LLM disabled, using rule_based"
    if status_code == "unknown_content_engine":
        return "Unknown content engine, using rule_based"
    return "LLM config incomplete, will fallback to rule_based"


def main() -> int:
    status = get_llm_config_status()
    content_engine_setting = get_runtime_config_value(
        "CONTENT_ENGINE_TYPE", default=status.requested_engine_type
    )

    print(f"CONTENT_ENGINE_TYPE: {status.requested_engine_type} via {content_engine_setting['source']}")
    print(f"Resolved engine: {status.resolved_engine_type}")
    print(f"LLM_PROVIDER: {status.llm_provider}")
    print(f"LLM_PROVIDER source: {status.llm_provider_source}")
    print(f"LLM_BASE_URL: {status.llm_base_url_status}")
    print(f"LLM_BASE_URL source: {status.llm_base_url_source}")
    print(f"LLM_MODEL: {status.llm_model_status}")
    print(f"LLM_MODEL source: {status.llm_model_source}")
    print(f"LLM_API_KEY: {status.llm_api_key_status}")
    print(f"LLM_API_KEY source: {status.llm_api_key_source}")
    print(f"LLM_API_KEY preview: {status.llm_api_key_preview}")
    print(f"LLM_TIMEOUT_SECONDS: {status.timeout_seconds:g}")
    print(f"LLM_MAX_RETRIES: {status.max_retries}")
    print(f"Status: {_status_text(status.status_code)}")

    if status.missing_fields:
        print(f"Missing: {', '.join(status.missing_fields)}")
    if status.invalid_fields:
        print(f"Invalid: {', '.join(status.invalid_fields)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
