from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services.settings_service import get_setting_record

DEFAULT_DB_PATH = ROOT_DIR / "data" / "zhongcaoji.db"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read one local app setting.")
    parser.add_argument("--key", required=True)
    parser.add_argument("--reveal", action="store_true")
    parser.add_argument("--db", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    db_path = Path(args.db) if args.db else DEFAULT_DB_PATH
    if not db_path.is_absolute():
        db_path = (ROOT_DIR / db_path).resolve()
    record = get_setting_record(args.key, db_path=db_path, reveal_secret=args.reveal)
    if not record:
        print(f"Setting not found: {args.key}")
        return 1
    print(f"{record['key']} = {record['value']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
