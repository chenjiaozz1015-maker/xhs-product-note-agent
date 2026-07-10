from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services.settings_service import is_secret_key, set_setting

DEFAULT_DB_PATH = ROOT_DIR / "data" / "zhongcaoji.db"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage local app settings.")
    parser.add_argument("--key", required=True)
    parser.add_argument("--value", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--db", default=None)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--secret", action="store_true")
    group.add_argument("--plain", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    secret = args.secret or (is_secret_key(args.key) and not args.plain)
    db_path = Path(args.db) if args.db else DEFAULT_DB_PATH
    if not db_path.is_absolute():
        db_path = (ROOT_DIR / db_path).resolve()
    set_setting(args.key, args.value, secret, args.description, db_path)
    suffix = " (secret)" if secret else ""
    print(f"Setting saved: {args.key}{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
