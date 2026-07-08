from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services.config_center_client import fetch_project_config, get_config_center_settings, load_runtime_config_token


def main() -> int:
    settings = get_config_center_settings()
    token_result = load_runtime_config_token()

    print("Config center runtime check")
    print()
    print(f"Project: {settings['project_code']}")
    print(f"Env: {settings['env']}")
    print(f"Token file: {settings['runtime_token_file']}")
    print(f"Runtime token: {'configured' if token_result['available'] else 'missing'}")

    if not token_result["available"]:
        print("Status: NOT READY")
        print(f"Reason: {token_result['error']}")
        return 1

    result = fetch_project_config()
    if result["available"]:
        config = result["config"] if isinstance(result["config"], dict) else {}
        config_keys = ", ".join(sorted(config.keys())) if config else "(empty)"
        print("Status: READY")
        print(f"HTTP status: {result['status_code']}")
        print(f"Config keys: {config_keys}")
        return 0

    print("Status: FAILED")
    print(f"Reason: {result['error']}")
    if result["status_code"] is not None:
        print(f"HTTP status: {result['status_code']}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
