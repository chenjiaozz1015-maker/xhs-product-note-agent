from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import sys
from typing import Any, Iterator

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import APP_VERSION, CONTENT_ENGINE_TYPE
from app.services import llm_content_service, settings_service
from app.services.content_engine_adapter import ContentGenerateInput, generate_content_with_rule_based
from app.services import runtime_config_service
from app.services.runtime_config_service import get_runtime_config_value
from scripts import batch_evaluate_content, compare_content_engines

DEFAULT_DB_PATH = ROOT_DIR / "data" / "zhongcaoji.db"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a local, manual LLM rollout check.")
    parser.add_argument("--skip-smoke", action="store_true")
    parser.add_argument("--skip-compare", action="store_true")
    parser.add_argument("--skip-batch", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--output")
    parser.add_argument("--db", default=None, help="SQLite database path, default data/zhongcaoji.db")
    return parser


def _resolve_db_path(raw_path: str | None) -> Path:
    selected = Path(raw_path) if raw_path else DEFAULT_DB_PATH
    return selected if selected.is_absolute() else (ROOT_DIR / selected).resolve()


@contextmanager
def _use_database(database_path: Path) -> Iterator[None]:
    original = settings_service.DATABASE_PATH
    original_reader = runtime_config_service.get_setting_record
    settings_service.DATABASE_PATH = database_path
    if not database_path.exists():
        runtime_config_service.get_setting_record = lambda *args, **kwargs: None
    try:
        yield
    finally:
        settings_service.DATABASE_PATH = original
        runtime_config_service.get_setting_record = original_reader


def _config_summary(status: llm_content_service.LLMConfigStatus) -> dict[str, Any]:
    content_setting = get_runtime_config_value("CONTENT_ENGINE_TYPE", default=CONTENT_ENGINE_TYPE)
    return {
        "content_engine_type": {
            "configured": bool(content_setting.get("value")),
            "source": content_setting.get("source", "missing"),
        },
        "llm_provider": {"configured": bool(status.llm_provider), "source": status.llm_provider_source},
        "llm_base_url": {
            "configured": status.llm_base_url_status == "configured",
            "source": status.llm_base_url_source,
        },
        "llm_model": {
            "configured": status.llm_model_status == "configured",
            "source": status.llm_model_source,
        },
        "llm_api_key": {
            "configured": status.llm_api_key_status == "configured",
            "source": status.llm_api_key_source,
        },
    }


def _sample_input() -> ContentGenerateInput:
    return ContentGenerateInput(
        product_name="水牛奶蛋糕",
        category="食品饮品",
        description="适合早餐和下午茶，口感松软，适合家里囤一点",
        content_type="真实测评",
        style="温柔日常",
    )


def _step(status: str, reason: str = "") -> dict[str, Any]:
    return {"status": status, "reason": reason}


def _run_smoke(content_input: ContentGenerateInput) -> dict[str, Any]:
    fallback = generate_content_with_rule_based(content_input).note_data
    result = llm_content_service.generate_openai_compatible_note_data(
        content_input=content_input,
        fallback_note_data=fallback,
    )
    if result.success:
        return _step("SUCCESS")
    return _step("FAILED", result.error_message or "llm_request_failed")


def _run_compare(content_input: ContentGenerateInput) -> dict[str, Any]:
    fallback = generate_content_with_rule_based(content_input).note_data
    result = llm_content_service.generate_openai_compatible_note_data(
        content_input=content_input,
        fallback_note_data=fallback,
    )
    if result.success:
        return _step("SUCCESS")
    return _step("FAILED", result.error_message or "llm_request_failed")


def _run_batch() -> dict[str, Any]:
    payload = batch_evaluate_content.evaluate_samples()
    if payload.get("llm_status") != "ready":
        return _step("FAILED", str(payload.get("llm_reason") or "llm_config_incomplete"))
    failed = any(sample.get("llm", {}).get("status") == "FAILED" for sample in payload.get("samples", []))
    return _step("FAILED" if failed else "SUCCESS", "llm_request_failed" if failed else "")


def run_check(args: argparse.Namespace) -> dict[str, Any]:
    database_path = _resolve_db_path(args.db)
    with _use_database(database_path):
        status = llm_content_service.get_llm_config_status("llm_openai_compatible")
        payload: dict[str, Any] = {
            "version": APP_VERSION,
            "config": _config_summary(status),
            "steps": {
                "config_check": _step("READY" if status.llm_config_ready else "NOT_READY", "" if status.llm_config_ready else "LLM config incomplete"),
                "smoke_check": _step("SKIPPED", "not run"),
                "compare": _step("SKIPPED", "not run"),
                "batch": _step("SKIPPED", "not run"),
            },
            "final_status": "READY_FOR_MANUAL_REVIEW" if status.llm_config_ready else "NOT_READY",
        }
        if not status.llm_config_ready:
            payload["missing"] = list(status.missing_fields)
            payload["invalid"] = list(status.invalid_fields)
            return payload

        content_input = _sample_input()
        if args.skip_smoke:
            payload["steps"]["smoke_check"] = _step("SKIPPED", "skipped by --skip-smoke")
        else:
            payload["steps"]["smoke_check"] = _run_smoke(content_input)
            if payload["steps"]["smoke_check"]["status"] == "FAILED":
                payload["final_status"] = "FAILED"
                return payload

        if args.skip_compare:
            payload["steps"]["compare"] = _step("SKIPPED", "skipped by --skip-compare")
        else:
            payload["steps"]["compare"] = _run_compare(content_input)
            if payload["steps"]["compare"]["status"] == "FAILED":
                payload["final_status"] = "FAILED"
                return payload

        if args.skip_batch:
            payload["steps"]["batch"] = _step("SKIPPED", "skipped by --skip-batch")
        else:
            payload["steps"]["batch"] = _run_batch()
            if payload["steps"]["batch"]["status"] == "FAILED":
                payload["final_status"] = "FAILED"
                return payload

        payload["final_status"] = "READY_FOR_MANUAL_REVIEW"
        return payload


def _render_text(payload: dict[str, Any]) -> str:
    lines = ["Local LLM Rollout Check", "", "Config source summary:"]
    for key, item in payload["config"].items():
        lines.append(f"{key.upper()}: {'configured' if item['configured'] else 'missing'} via {item['source']}")
    labels = [("config_check", "Config check"), ("smoke_check", "Smoke check"), ("compare", "Single product compare"), ("batch", "Batch evaluation")]
    for key, label in labels:
        item = payload["steps"][key]
        lines.extend(["", f"{label}:", f"Status: {item['status']}"])
        if item.get("reason"):
            lines.append(f"Reason: {item['reason']}")
    if payload.get("missing"):
        lines.append(f"Missing: {', '.join(payload['missing'])}")
    if payload.get("invalid"):
        lines.append(f"Invalid: {', '.join(payload['invalid'])}")
    lines.extend(["", f"Final status: {payload['final_status']}", "", "Next steps:"])
    lines.append("Review compare and batch outputs")
    lines.append("Keep CONTENT_ENGINE_TYPE=rule_based until manually approved")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = run_check(args)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) if args.format == "json" else _render_text(payload)
    print(rendered)
    if args.output:
        Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
