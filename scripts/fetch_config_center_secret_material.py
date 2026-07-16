from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services.config_center_client import (
    SECRET_MATERIAL_CONTENT_PATHS,
    build_secret_material_url,
    fetch_secret_material,
    get_config_center_settings,
    load_runtime_config_token,
)

DEFAULT_OUTPUT = ".config-center/test.secret-material.env"
ENV_ENTRY_PATTERN = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch config-center secret material to a protected local env file.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--raw", action="store_true", help="Request text/plain env content with raw=true.")
    return parser


def _extract_wrapped_content(raw_content: object) -> str:
    if isinstance(raw_content, dict):
        payload: object = raw_content
    else:
        text = str(raw_content or "")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return text
        if isinstance(payload, str):
            return payload

    if isinstance(payload, dict):
        for path in SECRET_MATERIAL_CONTENT_PATHS:
            current: object = payload
            for key in path:
                current = current.get(key) if isinstance(current, dict) else None
            if isinstance(current, str):
                return current
    return ""


def _find_env_keys(content: str) -> list[str]:
    keys: list[str] = []
    for line in content.splitlines():
        match = ENV_ENTRY_PATTERN.match(line)
        if match:
            keys.append(match.group(1))
    return keys


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_config_center_settings()
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = (ROOT_DIR / output_path).resolve()
    token_result = load_runtime_config_token()

    if args.dry_run:
        print("Config center secret-material dry run")
        print(f"URL: {build_secret_material_url(settings, raw=args.raw)}")
        print(f"Project: {settings['project_code']}")
        print(f"Env: {settings['env']}")
        print(f"Runtime token: {'configured' if token_result['available'] else 'missing'}")
        print(f"Output: {args.output}")
        print("No request was sent.")
        return 0

    if not token_result["available"]:
        print(f"Secret material fetch skipped: {token_result['error']}")
        return 1
    if output_path.exists() and not args.overwrite:
        print("Secret material file already exists. Use --overwrite to replace it.")
        return 1

    result = fetch_secret_material(raw=args.raw)
    if not result["available"]:
        print(f"Secret material fetch failed: {result['error']}")
        if result.get("status_code") is not None:
            print(f"HTTP status: {result['status_code']}")
        return 1

    secret_content = _extract_wrapped_content(result.get("content", ""))
    secret_keys = _find_env_keys(secret_content)
    if not secret_keys:
        print("Secret material invalid: no env entries found")
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(secret_content, encoding="utf-8")
    print(f"Secret material written: {args.output}")
    if "LLM_API_KEY" in secret_keys:
        print("Secret keys found: LLM_API_KEY")
    else:
        print(f"Secret keys found: {', '.join(secret_keys)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
