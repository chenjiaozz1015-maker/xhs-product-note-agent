from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services.settings_service import list_settings

DEFAULT_DB_PATH = ROOT_DIR / "data" / "zhongcaoji.db"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="List local app settings.")
    parser.add_argument("--reveal", action="store_true")
    parser.add_argument("--db", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    db_path = Path(args.db) if args.db else DEFAULT_DB_PATH
    if not db_path.is_absolute():
        db_path = (ROOT_DIR / db_path).resolve()
    records = list_settings(db_path=db_path, reveal_secret=args.reveal)
    if not records:
        print("No app settings found.")
        return 0
    for record in records:
        print(
            " | ".join(
                [
                    f"key={record['key']}",
                    f"value={record['value']}",
                    f"is_secret={int(record['is_secret'])}",
                    f"description={record['description'] or '-'}",
                    f"updated_at={record['updated_at']}",
                ]
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
