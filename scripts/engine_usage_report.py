from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import APP_VERSION

DEFAULT_DB_PATH = ROOT_DIR / "data" / "zhongcaoji.db"
DEFAULT_LIMIT = 30
KNOWN_FALLBACK_REASONS = (
    "llm_timeout",
    "llm_config_missing",
    "llm_invalid_json",
    "llm_schema_invalid",
    "llm_request_failed",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only content engine usage report.")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Number of recent records to inspect.")
    parser.add_argument("--email", default="", help="Filter by user email.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format.")
    parser.add_argument("--db", default=None, help="SQLite database path. Defaults to data/zhongcaoji.db")
    return parser


def _resolve_db_path(raw_path: str | None) -> Path:
    selected = Path(raw_path) if raw_path else DEFAULT_DB_PATH
    return selected if selected.is_absolute() else (ROOT_DIR / selected).resolve()


def _print(message: str = "") -> None:
    sys.stdout.write(f"{message}\n")


def _error(message: str) -> int:
    sys.stderr.write(f"{message}\n")
    return 1


def _connect_read_only(database_path: Path) -> sqlite3.Connection:
    if not database_path.exists():
        raise FileNotFoundError(
            "Database file not found. Run from the project root, or pass --db with a valid SQLite path."
        )
    uri = f"file:{database_path.as_posix()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row["name"]) for row in rows}


def _select_expression(columns: set[str], column_name: str, alias: str | None = None) -> str:
    selected_alias = alias or column_name
    if column_name in columns:
        return f"gr.{column_name} AS {selected_alias}"
    return f"NULL AS {selected_alias}"


def _normalize_engine_type(value: Any) -> str:
    return str(value or "").strip()


def _normalize_fallback_used(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value in (None, "", 0, "0"):
        return False
    return bool(int(value)) if str(value).isdigit() else bool(value)


def _load_records(
    connection: sqlite3.Connection,
    *,
    limit: int,
    email: str,
) -> list[dict[str, Any]]:
    user_columns = _table_columns(connection, "users")
    record_columns = _table_columns(connection, "generation_records")
    if not record_columns:
        raise LookupError(
            "generation_records table not found. Please run the app once to initialize the database schema."
        )

    email_expression = "u.email AS email" if "email" in user_columns else "NULL AS email"
    query = f"""
        SELECT
            gr.created_at,
            {email_expression},
            gr.product_name,
            gr.category,
            {_select_expression(record_columns, "requested_engine_type")},
            {_select_expression(record_columns, "content_engine_type")},
            {_select_expression(record_columns, "content_fallback_used")},
            {_select_expression(record_columns, "content_fallback_reason")}
        FROM generation_records gr
        LEFT JOIN users u ON u.id = gr.user_id
        WHERE (? = '' OR u.email = ?)
        ORDER BY datetime(gr.created_at) DESC, gr.id DESC
        LIMIT ?
    """
    rows = connection.execute(query, (email, email, max(int(limit), 1))).fetchall()
    records: list[dict[str, Any]] = []
    for row in rows:
        record = dict(row)
        record["requested_engine_type"] = _normalize_engine_type(record.get("requested_engine_type"))
        record["content_engine_type"] = _normalize_engine_type(record.get("content_engine_type"))
        record["content_fallback_used"] = _normalize_fallback_used(record.get("content_fallback_used"))
        record["content_fallback_reason"] = _normalize_engine_type(record.get("content_fallback_reason"))
        records.append(record)
    return records


def _summarize_records(records: list[dict[str, Any]]) -> tuple[dict[str, int], dict[str, int]]:
    summary = {
        "total_records": len(records),
        "rule_based": 0,
        "llm": 0,
        "fallback": 0,
        "unknown": 0,
    }
    fallback_reasons = {reason: 0 for reason in KNOWN_FALLBACK_REASONS}

    for record in records:
        engine_type = _normalize_engine_type(record.get("content_engine_type"))
        if engine_type == "rule_based":
            summary["rule_based"] += 1
        elif engine_type == "llm_openai_compatible":
            summary["llm"] += 1
        else:
            summary["unknown"] += 1

        if record.get("content_fallback_used"):
            summary["fallback"] += 1
            reason = _normalize_engine_type(record.get("content_fallback_reason")) or "unknown"
            fallback_reasons[reason] = fallback_reasons.get(reason, 0) + 1

    return summary, fallback_reasons


def _build_payload(database_path: Path, email: str, limit: int, records: list[dict[str, Any]]) -> dict[str, Any]:
    summary, fallback_reasons = _summarize_records(records)
    return {
        "version": APP_VERSION,
        "database": str(database_path),
        "scope": email or "all users",
        "limit": limit,
        "summary": summary,
        "fallback_reasons": fallback_reasons,
        "records": [
            {
                "created_at": record.get("created_at"),
                "email": record.get("email"),
                "product_name": record.get("product_name"),
                "category": record.get("category"),
                "requested_engine_type": record.get("requested_engine_type"),
                "content_engine_type": record.get("content_engine_type"),
                "fallback_used": bool(record.get("content_fallback_used")),
                "fallback_reason": record.get("content_fallback_reason") or "",
            }
            for record in records
        ],
    }


def _render_text(payload: dict[str, Any]) -> str:
    lines = [
        "Content Engine Usage Report",
        "",
        f"Version: {payload['version']}",
        f"Database: {payload['database']}",
        f"Scope: {payload['scope']}",
        f"Limit: {payload['limit']}",
        "",
        "Summary:",
        f"Total records: {payload['summary']['total_records']}",
        f"Rule-based: {payload['summary']['rule_based']}",
        f"LLM: {payload['summary']['llm']}",
        f"Fallback: {payload['summary']['fallback']}",
        f"Unknown / old records: {payload['summary']['unknown']}",
        "",
        "Fallback reasons:",
    ]
    for reason, count in payload["fallback_reasons"].items():
        lines.append(f"{reason}: {count}")

    lines.extend(["", "Recent records:"])
    if not payload["records"]:
        lines.append("No generation records found for the selected scope.")
        return "\n".join(lines)

    for record in payload["records"]:
        parts = [
            str(record.get("created_at") or "-"),
            str(record.get("email") or "-"),
            str(record.get("product_name") or "-"),
            str(record.get("category") or "-"),
            str(record.get("content_engine_type") or "unknown"),
            f"fallback={'yes' if record.get('fallback_used') else 'no'}",
        ]
        if record.get("fallback_reason"):
            parts.append(f"reason={record['fallback_reason']}")
        lines.append(" | ".join(parts))

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    limit = max(int(args.limit), 1)
    email = str(args.email or "").strip()
    database_path = _resolve_db_path(args.db)

    try:
        with _connect_read_only(database_path) as connection:
            records = _load_records(connection, limit=limit, email=email)
    except (FileNotFoundError, LookupError) as exc:
        return _error(str(exc))
    except sqlite3.Error:
        return _error("Failed to read SQLite database. Please verify the database path and schema.")

    payload = _build_payload(database_path, email, limit, records)
    if args.format == "json":
        _print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _print(_render_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
