from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services import llm_content_service
from app.services.content_engine_adapter import ContentGenerateInput, generate_content_with_rule_based


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare rule_based and llm_openai_compatible content outputs.")
    parser.add_argument("--product-name", default="水牛奶蛋糕")
    parser.add_argument("--category", default="食品饮品")
    parser.add_argument("--description", default="适合早餐和下午茶，口感松软，适合家里囤一点")
    parser.add_argument("--content-type", default="真实测评")
    parser.add_argument("--style", default="温柔日常")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--output")
    return parser


def _normalize_selling_points(values: list[Any]) -> list[str]:
    points: list[str] = []
    for value in values[:3]:
        if isinstance(value, dict):
            title = str(value.get("title", "")).strip()
            description = str(value.get("description", "")).strip()
            text = " ".join(part for part in (title, description) if part).strip()
            if text:
                points.append(text)
            continue
        text = str(value).strip()
        if text:
            points.append(text)
    return points


def _note_summary(note_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "titles": list(note_data.get("note_titles", []))[:5],
        "body": str(note_data.get("note_body", "")).strip(),
        "hashtags": list(note_data.get("hashtags", []))[:8],
        "selling_points": _normalize_selling_points(list(note_data.get("selling_points", []))),
    }


def _print_note_block(title: str, note_data: dict[str, Any]) -> None:
    summary = _note_summary(note_data)
    print(f"{title}:")
    print("Titles:")
    for item in summary["titles"]:
        print(f"- {item}")
    print("\nBody:")
    print(summary["body"])
    print("\nHashtags:")
    print(" ".join(summary["hashtags"]))
    print("\nSelling points:")
    for item in summary["selling_points"]:
        print(f"- {item}")


def _build_result_payload(
    content_input: ContentGenerateInput,
    rule_based_note_data: dict[str, Any],
    llm_status: llm_content_service.LLMConfigStatus,
    llm_result: llm_content_service.LLMContentResult | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "input": {
            "product_name": content_input.product_name,
            "category": content_input.category,
            "description": content_input.description,
            "content_type": content_input.content_type,
            "style": content_input.style,
        },
        "rule_based": _note_summary(rule_based_note_data),
        "llm": {
            "provider": llm_status.llm_provider,
            "base_url": llm_status.llm_base_url_status,
            "model": llm_status.llm_model_status,
            "api_key": llm_status.llm_api_key_preview,
            "status": "SKIPPED",
            "reason": "llm_config_incomplete",
            "missing": list(llm_status.missing_fields),
            "invalid": list(llm_status.invalid_fields),
            "result": None,
        },
    }

    if not llm_status.llm_config_ready:
        return payload

    if llm_result is None:
        return payload

    if llm_result.success:
        payload["llm"]["status"] = "SUCCESS"
        payload["llm"]["reason"] = None
        payload["llm"]["missing"] = []
        payload["llm"]["invalid"] = []
        payload["llm"]["result"] = _note_summary(llm_result.note_data)
        return payload

    payload["llm"]["status"] = "FAILED"
    payload["llm"]["reason"] = llm_result.error_message or "llm_request_failed"
    payload["llm"]["missing"] = []
    payload["llm"]["invalid"] = []
    return payload


def _write_output(path: str, payload: dict[str, Any]) -> None:
    output_path = Path(path)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    content_input = ContentGenerateInput(
        product_name=args.product_name,
        category=args.category,
        description=args.description,
        content_type=args.content_type,
        style=args.style,
    )

    rule_based_result = generate_content_with_rule_based(content_input)
    rule_based_note_data = rule_based_result.note_data
    llm_status = llm_content_service.get_llm_config_status("llm_openai_compatible")
    llm_result: llm_content_service.LLMContentResult | None = None

    if llm_status.llm_config_ready:
        llm_result = llm_content_service.generate_openai_compatible_note_data(
            content_input=content_input,
            fallback_note_data=rule_based_note_data,
        )

    payload = _build_result_payload(content_input, rule_based_note_data, llm_status, llm_result)

    if args.format == "json":
        rendered = json.dumps(payload, ensure_ascii=False, indent=2)
        print(rendered)
    else:
        print("Content Engine Compare\n")
        print("Input:")
        print(f"Product: {content_input.product_name}")
        print(f"Category: {content_input.category}")
        print(f"Content type: {content_input.content_type}")
        print(f"Style: {content_input.style}\n")

        _print_note_block("Rule-based result", rule_based_note_data)
        print("\nLLM result:")
        print(f"Provider: {llm_status.llm_provider}")
        print(f"Base URL: {llm_status.llm_base_url_status}")
        print(f"Model: {llm_status.llm_model_status}")
        print(f"API Key: {llm_status.llm_api_key_status}, {llm_status.llm_api_key_preview}")

        llm_payload = payload["llm"]
        print(f"Status: {llm_payload['status']}")
        if llm_payload["reason"]:
            reason_map = {
                "llm_config_incomplete": "LLM config incomplete",
                "llm_timeout": "llm_timeout",
                "llm_request_failed": "llm_request_failed",
                "llm_invalid_json": "llm_invalid_json",
                "llm_schema_invalid": "llm_schema_invalid",
            }
            print(f"Reason: {reason_map.get(str(llm_payload['reason']), llm_payload['reason'])}")
        if llm_payload["missing"]:
            print(f"Missing: {', '.join(llm_payload['missing'])}")
        if llm_payload["invalid"]:
            print(f"Invalid: {', '.join(llm_payload['invalid'])}")

        if llm_payload["status"] == "SKIPPED":
            print("No LLM request was sent.")
        elif llm_payload["status"] == "FAILED":
            print("Fallback:")
            print("Rule-based result is still available.")
        else:
            print()
            _print_note_block("LLM result detail", llm_result.note_data if llm_result else {})

    if args.output:
        _write_output(args.output, payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
