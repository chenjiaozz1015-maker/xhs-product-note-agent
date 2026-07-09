from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services import db
from app.services.auth_service import get_user_by_email, hash_password

DEFAULT_DB_PATH = ROOT_DIR / "data" / "zhongcaoji.db"


def _print(message: str = "") -> None:
    sys.stdout.write(f"{message}\n")


def _error(message: str) -> int:
    sys.stderr.write(f"{message}\n")
    return 1


def _resolve_db_path(raw_path: str | None) -> Path:
    selected = Path(raw_path) if raw_path else DEFAULT_DB_PATH
    return selected if selected.is_absolute() else (ROOT_DIR / selected).resolve()


def _configure_database(database_path: Path) -> None:
    if not database_path.exists():
        raise FileNotFoundError(f"Database not found: {database_path}")
    db.DATABASE_PATH = database_path
    db.init_db(database_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reset a user's password from the command line.")
    parser.add_argument("--email", required=True, help="User email")
    parser.add_argument("--password", required=True, help="New password")
    parser.add_argument("--db", default=None, help="SQLite database path, default data/zhongcaoji.db")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if len(args.password) < 6:
        return _error("Password must be at least 6 characters")

    database_path = _resolve_db_path(args.db)
    try:
        _configure_database(database_path)
    except FileNotFoundError as exc:
        return _error(str(exc))

    user = get_user_by_email(args.email)
    if not user:
        return _error(f"User not found: {args.email}")

    new_password_hash = hash_password(args.password)
    with db.get_connection() as connection:
        connection.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (new_password_hash, int(user["id"])),
        )
        connection.commit()

    _print(f"Password reset succeeded for {args.email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
