from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import (
    CONTENT_ENGINE_TYPE,
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MAX_RETRIES_RAW,
    LLM_MODEL,
    LLM_PROVIDER,
    LLM_TIMEOUT_SECONDS_RAW,
)
from app.services.config_center_client import build_runtime_token_file_path

DEFAULT_DB_PATH = ROOT_DIR / "data" / "zhongcaoji.db"
DEFAULT_SECRET_MATERIAL_FILE = ROOT_DIR / ".config-center" / "test.secret-material.env"
SUPPORTED_PROVIDERS = {"openai_compatible", "deepseek"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only LLM gray rollout readiness check.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    parser.add_argument("--output", help="Write JSON report to this file.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    return parser


def _resolve_path(raw_path: str | Path) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (ROOT_DIR / path).resolve()


def _read_app_setting(db_path: Path, key: str) -> dict[str, Any] | None:
    if not db_path.exists():
        return None
    try:
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as connection:
            connection.row_factory = sqlite3.Row
            table = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='app_settings'"
            ).fetchone()
            if not table:
                return None
            row = connection.execute(
                "SELECT key, value, is_secret FROM app_settings WHERE key = ?",
                (key,),
            ).fetchone()
    except sqlite3.Error:
        return None
    return dict(row) if row else None


def _get_config_value(db_path: Path, key: str, default: str = "") -> dict[str, Any]:
    env_value = os.getenv(key, "").strip()
    if env_value:
        return {"value": env_value, "source": "env", "configured": True}

    record = _read_app_setting(db_path, key)
    if record:
        value = str(record.get("value") or "").strip()
        return {
            "value": value,
            "source": "app_settings",
            "configured": bool(value),
            "is_secret": bool(record.get("is_secret")),
        }

    default_value = str(default or "").strip()
    return {
        "value": default_value,
        "source": "default" if default_value else "missing",
        "configured": bool(default_value),
    }


def _app_settings_summary(db_path: Path) -> dict[str, Any]:
    if not db_path.exists():
        return {"ready": False, "count": 0}
    try:
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as connection:
            table = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='app_settings'"
            ).fetchone()
            if not table:
                return {"ready": False, "count": 0}
            count = connection.execute("SELECT COUNT(*) FROM app_settings").fetchone()[0]
    except sqlite3.Error:
        return {"ready": False, "count": 0}
    return {"ready": True, "count": int(count)}


def _generation_records_summary(db_path: Path) -> dict[str, Any]:
    if not db_path.exists():
        return {"available": False, "recent_count": 0}
    try:
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as connection:
            table = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='generation_records'"
            ).fetchone()
            if not table:
                return {"available": False, "recent_count": 0}
            count = connection.execute("SELECT COUNT(*) FROM generation_records").fetchone()[0]
    except sqlite3.Error:
        return {"available": False, "recent_count": 0}
    return {"available": True, "recent_count": int(count)}


def _safe_float(value: str) -> bool:
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def _safe_int(value: str) -> bool:
    try:
        return int(value) >= 0
    except (TypeError, ValueError):
        return False


def _llm_config_summary(db_path: Path) -> dict[str, Any]:
    provider = _get_config_value(db_path, "LLM_PROVIDER", LLM_PROVIDER)
    base_url = _get_config_value(db_path, "LLM_BASE_URL", LLM_BASE_URL)
    model = _get_config_value(db_path, "LLM_MODEL", LLM_MODEL)
    api_key = _get_config_value(db_path, "LLM_API_KEY", LLM_API_KEY)
    timeout = _get_config_value(db_path, "LLM_TIMEOUT_SECONDS", LLM_TIMEOUT_SECONDS_RAW)
    retries = _get_config_value(db_path, "LLM_MAX_RETRIES", LLM_MAX_RETRIES_RAW)

    missing: list[str] = []
    invalid: list[str] = []
    if provider["value"] not in SUPPORTED_PROVIDERS:
        invalid.append("LLM_PROVIDER")
    if not base_url["value"]:
        missing.append("LLM_BASE_URL")
    if not model["value"]:
        missing.append("LLM_MODEL")
    if not api_key["value"]:
        missing.append("LLM_API_KEY")
    if timeout["value"] and not _safe_float(str(timeout["value"])):
        invalid.append("LLM_TIMEOUT_SECONDS")
    if retries["value"] and not _safe_int(str(retries["value"])):
        invalid.append("LLM_MAX_RETRIES")

    return {
        "ready": not missing and not invalid,
        "provider": {"configured": bool(provider["value"]), "source": provider["source"]},
        "base_url": {"configured": bool(base_url["value"]), "source": base_url["source"]},
        "model": {"configured": bool(model["value"]), "source": model["source"]},
        "api_key": {"configured": bool(api_key["value"]), "source": api_key["source"]},
        "missing": missing,
        "invalid": invalid,
    }


def _latest_rollout_report() -> dict[str, Any]:
    reports = sorted(ROOT_DIR.glob("local_llm_rollout_report*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not reports:
        return {"present": False, "smoke_success": False, "path": ""}
    report_path = reports[0]
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"present": True, "smoke_success": False, "path": str(report_path.relative_to(ROOT_DIR))}
    steps = payload.get("steps", {}) if isinstance(payload, dict) else {}
    smoke = steps.get("smoke_check", {}) if isinstance(steps, dict) else {}
    return {
        "present": True,
        "smoke_success": smoke.get("status") == "SUCCESS",
        "path": str(report_path.relative_to(ROOT_DIR)),
    }


def build_report(db_path: Path) -> dict[str, Any]:
    content_engine = _get_config_value(db_path, "CONTENT_ENGINE_TYPE", CONTENT_ENGINE_TYPE)
    llm = _llm_config_summary(db_path)
    runtime_token_file = build_runtime_token_file_path()
    secret_material_file = DEFAULT_SECRET_MATERIAL_FILE
    runbook = ROOT_DIR / "docs" / "llm_gray_rollout_runbook.md"
    observation_script = ROOT_DIR / "scripts" / "engine_usage_report.py"
    rollout_report = _latest_rollout_report()

    missing: list[str] = []
    if content_engine["value"] != "rule_based":
        missing.append("CONTENT_ENGINE_TYPE should remain rule_based before manual approval")
    if not llm["ready"]:
        missing.extend(llm["missing"])
        missing.extend(llm["invalid"])
    if not runtime_token_file.exists():
        missing.append("runtime token file")
    if not secret_material_file.exists():
        missing.append("secret-material file")
    if not runbook.exists():
        missing.append("docs/llm_gray_rollout_runbook.md")
    if not observation_script.exists():
        missing.append("scripts/engine_usage_report.py")
    if not rollout_report["smoke_success"]:
        missing.append("local rollout smoke success not confirmed")

    return {
        "current_engine": str(content_engine["value"]),
        "current_engine_source": content_engine["source"],
        "llm_config": "READY" if llm["ready"] else "NOT_READY",
        "llm_api_key": "configured" if llm["api_key"]["configured"] else "missing",
        "llm_api_key_source": llm["api_key"]["source"],
        "app_settings": _app_settings_summary(db_path),
        "runtime_token_file": "present" if runtime_token_file.exists() else "missing",
        "secret_material_file": "present" if secret_material_file.exists() else "missing",
        "runbook": "present" if runbook.exists() else "missing",
        "observation_script": "present" if observation_script.exists() else "missing",
        "local_rollout_report": rollout_report,
        "generation_records": _generation_records_summary(db_path),
        "recommendation": "READY_FOR_MANUAL_DECISION" if not missing else "NOT_READY",
        "missing": sorted(set(missing)),
    }


def render_text(report: dict[str, Any]) -> str:
    lines = [
        "LLM Gray Rollout Readiness",
        "",
        f"Current engine: {report['current_engine']}",
        f"LLM config: {report['llm_config']}",
        f"LLM API key: {report['llm_api_key']}",
        f"Runtime token file: {report['runtime_token_file']}",
        f"Secret material file: {report['secret_material_file']}",
        f"Runbook: {report['runbook']}",
        f"Observation script: {report['observation_script']}",
        f"Recommendation: {report['recommendation']}",
    ]
    if report["missing"]:
        lines.extend(["", "Missing:"])
        lines.extend(str(item) for item in report["missing"])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report(_resolve_path(args.db))
    rendered_json = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered_json if args.json else render_text(report))
    if args.output:
        Path(args.output).write_text(rendered_json, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
