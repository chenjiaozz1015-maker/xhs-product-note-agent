from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services import llm_content_service
from app.services.content_engine_adapter import ContentGenerateInput
from app.services.content_generator import generate_note_payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manual LLM smoke check for OpenAI-compatible providers.")
    parser.add_argument("--product-name", default="水牛奶蛋糕")
    parser.add_argument("--category", default="食品饮品")
    parser.add_argument("--description", default="适合早餐和下午茶，口感松软，适合家里囤一点")
    parser.add_argument("--content-type", default="真实测评")
    parser.add_argument("--style", default="温柔日常")
    return parser


def _print_summary(note_data: dict[str, object]) -> None:
    print("Generated titles:")
    for title in list(note_data.get("note_titles", []))[:5]:
        print(f"- {title}")

    body = str(note_data.get("note_body", "")).strip()
    print("\nBody preview:")
    print(body[:180])

    hashtags = " ".join(list(note_data.get("hashtags", []))[:8])
    print("\nHashtags:")
    print(hashtags)

    print("\nSelling points:")
    for point in list(note_data.get("selling_points", []))[:3]:
        print(f"- {point}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    print("LLM Smoke Check\n")

    status = llm_content_service.get_llm_config_status("llm_openai_compatible")
    print(f"Content engine: llm_openai_compatible")
    print(f"Provider: {status.llm_provider}")
    print(f"Base URL: {status.llm_base_url_status}")
    print(f"Model: {status.llm_model_status}")
    print(f"API Key: {status.llm_api_key_status}, {status.llm_api_key_preview}")

    if not status.llm_config_ready:
        print("\nStatus: SKIPPED")
        print("Reason: LLM config incomplete")
        if status.missing_fields:
            print(f"Missing: {', '.join(status.missing_fields)}")
        if status.invalid_fields:
            print(f"Invalid: {', '.join(status.invalid_fields)}")
        print("No request was sent.")
        return 0

    content_input = ContentGenerateInput(
        product_name=args.product_name,
        category=args.category,
        description=args.description,
        content_type=args.content_type,
        style=args.style,
    )
    fallback_note_data = generate_note_payload(
        description=args.description,
        content_type=args.content_type,
        style=args.style,
        product_name=args.product_name,
        category=args.category,
    )
    result = llm_content_service.generate_openai_compatible_note_data(
        content_input=content_input,
        fallback_note_data=fallback_note_data,
    )

    if not result.success:
        print("\nStatus: FAILED")
        print(f"Reason: {result.error_message or 'llm_request_failed'}")
        print("Fallback: rule_based is still available for normal generation")
        return 1

    print("\nStatus: SUCCESS\n")
    _print_summary(result.note_data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
