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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap internal config-center project.")
    parser.add_argument("--dry-run", action="store_true", help="Print request summary without sending request.")
    parser.add_argument("--yes", action="store_true", help="Confirm and send bootstrap request.")
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
    if status_code is not None:
        print(f"status_code: {status_code}")


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
    try:
        status_code, _ = _post_bootstrap(config["base_url"], payload)
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
        return 0

    print("Config center bootstrap failed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
