from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib import error, request

ROOT_DIR = Path(__file__).resolve().parents[1]

DEFAULT_BASE_URL = "http://39.106.61.160:28081"
DEFAULT_PROJECT_CODE = "zhongcaoji"
DEFAULT_RUNTIME = "python"
DEFAULT_LOCAL_WORKSPACE_ROOT = str(ROOT_DIR)
DEFAULT_RUNTIME_TOKEN_FILE = ".config-center/test.runtime-token.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap internal config-center project.")
    parser.add_argument("--dry-run", action="store_true", help="Print request summary without sending request.")
    parser.add_argument("--yes", action="store_true", help="Confirm and send bootstrap request.")
    parser.add_argument(
        "--overwrite-token",
        action="store_true",
        help="Allow replacing an existing runtime token file after successful bootstrap.",
    )
    return parser


def _get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _build_config() -> dict[str, str]:
    return {
        "base_url": _get_env("CONFIG_CENTER_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        "project_code": _get_env("CONFIG_CENTER_PROJECT_CODE", DEFAULT_PROJECT_CODE) or DEFAULT_PROJECT_CODE,
        "runtime": _get_env("CONFIG_CENTER_RUNTIME", DEFAULT_RUNTIME) or DEFAULT_RUNTIME,
        "local_workspace_root": _get_env(
            "CONFIG_CENTER_LOCAL_WORKSPACE_ROOT",
            DEFAULT_LOCAL_WORKSPACE_ROOT,
        )
        or DEFAULT_LOCAL_WORKSPACE_ROOT,
        "invite_code": _get_env("CONFIG_CENTER_INVITE_CODE"),
        "runtime_token_file": _get_env("CONFIG_CENTER_RUNTIME_TOKEN_FILE", DEFAULT_RUNTIME_TOKEN_FILE)
        or DEFAULT_RUNTIME_TOKEN_FILE,
    }


def build_request_payload(config: dict[str, str]) -> dict[str, str]:
    return {
        "projectCode": config["project_code"],
        "runtime": config["runtime"],
        "inviteCode": config["invite_code"],
        "localWorkspaceRoot": config["local_workspace_root"],
    }


def _post_bootstrap(base_url: str, payload: dict[str, str]) -> tuple[int, str]:
    url = f"{base_url}/internal/config-center/v1/projects/bootstrap"
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=15) as response:
        return int(response.getcode()), response.read().decode("utf-8", errors="replace")


def _print_summary(config: dict[str, str], *, status_code: int | None = None) -> None:
    print(f"projectCode: {config['project_code']}")
    print(f"runtime: {config['runtime']}")
    print(f"localWorkspaceRoot: {config['local_workspace_root']}")
    print(f"inviteCode: {'configured' if config['invite_code'] else 'missing'}")
    print(f"runtimeTokenFile: {config['runtime_token_file']}")
    if status_code is not None:
        print(f"status_code: {status_code}")


def _runtime_token_path(config: dict[str, str]) -> Path:
    token_path = Path(config["runtime_token_file"])
    return token_path if token_path.is_absolute() else ROOT_DIR / token_path


def _extract_runtime_config_token(payload: object) -> str:
    candidate_paths = [
        ("runtimeConfigToken",),
        ("data", "runtimeConfigToken"),
        ("result", "runtimeConfigToken"),
        ("token", "runtimeConfigToken"),
        ("runtimeTokenFile", "runtimeConfigToken"),
        ("data", "runtimeTokenFile", "runtimeConfigToken"),
        ("result", "runtimeTokenFile", "runtimeConfigToken"),
        ("token", "runtimeTokenFile", "runtimeConfigToken"),
    ]
    for path in candidate_paths:
        current = payload
        for key in path:
            if not isinstance(current, dict) or key not in current:
                current = None
                break
            current = current[key]
        token = str(current).strip() if current is not None else ""
        if token:
            return token
    return ""


def _has_string_runtime_token_file(payload: object) -> bool:
    containers = [payload]
    if isinstance(payload, dict):
        containers.extend(payload.get(key) for key in ("data", "result", "token"))
    return any(isinstance(item, dict) and isinstance(item.get("runtimeTokenFile"), str) for item in containers)


def _top_level_keys(payload: object) -> str:
    if isinstance(payload, dict):
        keys = sorted(str(key) for key in payload.keys())
        return ", ".join(keys) if keys else "(empty)"
    return "(non-object-response)"


def _write_runtime_token_file(config: dict[str, str], token: str, *, overwrite: bool) -> bool:
    token_path = _runtime_token_path(config)
    if token_path.exists() and not overwrite:
        print("Runtime token file already exists. Use --overwrite-token to replace it.")
        return False

    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(
        json.dumps({"runtimeConfigToken": token}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Runtime token file written: {config['runtime_token_file']}")
    return True


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = _build_config()

    if args.dry_run:
        print("Config center bootstrap dry run")
        _print_summary(config)
        print("No request was sent.")
        return 0

    if not args.yes:
        print(f"This will bootstrap config-center project: {config['project_code']}")
        print("Run again with --yes to confirm.")
        return 0

    if not config["invite_code"]:
        print("CONFIG_CENTER_INVITE_CODE is required")
        return 1

    payload = build_request_payload(config)
    status_code = 0
    response_body = ""
    try:
        status_code, response_body = _post_bootstrap(config["base_url"], payload)
        success = 200 <= status_code < 300
    except error.HTTPError as exc:
        status_code = int(exc.code)
        success = False
    except error.URLError:
        success = False
    except Exception:
        success = False

    _print_summary(config, status_code=status_code)
    if success:
        print("Config center bootstrap succeeded")
        try:
            response_payload = json.loads(response_body) if response_body else {}
        except json.JSONDecodeError:
            response_payload = {}

        runtime_config_token = _extract_runtime_config_token(response_payload)
        if runtime_config_token:
            _write_runtime_token_file(config, runtime_config_token, overwrite=args.overwrite_token)
        else:
            print("Config center bootstrap succeeded, but runtimeConfigToken was not found in response.")
            if _has_string_runtime_token_file(response_payload):
                print("runtimeTokenFile returned but runtimeConfigToken was not found inside it.")
            print(f"Response keys: {_top_level_keys(response_payload)}")
        return 0

    print("Config center bootstrap failed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
