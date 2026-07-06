from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import APP_VERSION
from app.services import llm_content_service
from app.services.content_engine_adapter import ContentGenerateInput, generate_content_with_rule_based


DEFAULT_SAMPLES = [
    {
        "product_name": "水牛奶蛋糕",
        "category": "食品饮品",
        "description": "适合早餐和下午茶，口感松软，适合家里囤一点",
        "content_type": "真实测评",
        "style": "温柔日常",
    },
    {
        "product_name": "挂耳咖啡",
        "category": "食品饮品",
        "description": "办公室和早八都适合，冲泡方便，口感顺滑",
        "content_type": "种草推荐",
        "style": "生活方式",
    },
    {
        "product_name": "护手霜",
        "category": "美妆护肤",
        "description": "秋冬随身带，不黏腻，适合通勤补涂",
        "content_type": "真实测评",
        "style": "温柔日常",
    },
    {
        "product_name": "口红",
        "category": "美妆护肤",
        "description": "日常通勤显气色，薄涂厚涂都好看",
        "content_type": "种草推荐",
        "style": "清新简约",
    },
    {
        "product_name": "保温杯",
        "category": "家居日用",
        "description": "通勤带着方便，容量刚好，适合办公室和外出",
        "content_type": "真实测评",
        "style": "干货清单",
    },
    {
        "product_name": "收纳盒",
        "category": "家居日用",
        "description": "桌面小物分类收纳，拿取方便，让桌面更整洁",
        "content_type": "种草推荐",
        "style": "可爱手账",
    },
    {
        "product_name": "厨房清洁湿巾",
        "category": "家居日用",
        "description": "日常厨房清洁更省心，适合擦灶台和油污区域",
        "content_type": "真实测评",
        "style": "干货清单",
    },
    {
        "product_name": "坚果零食",
        "category": "食品饮品",
        "description": "小包装方便携带，追剧和办公室解馋都适合",
        "content_type": "种草推荐",
        "style": "生活方式",
    },
]

REASON_LABELS = {
    "llm_config_incomplete": "LLM config incomplete",
    "llm_timeout": "llm_timeout",
    "llm_request_failed": "llm_request_failed",
    "llm_invalid_json": "llm_invalid_json",
    "llm_schema_invalid": "llm_schema_invalid",
    "only_rule_based": "Skipped by --only rule_based",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Batch-evaluate rule_based and llm_openai_compatible content quality.")
    parser.add_argument("--format", choices=("text", "markdown", "json"), default="text")
    parser.add_argument("--output")
    parser.add_argument("--only", choices=("all", "rule_based", "llm"), default="all")
    return parser


def _normalize_selling_points(values: list[Any]) -> list[str]:
    points: list[str] = []
    for value in values[:3]:
        if isinstance(value, dict):
            title = str(value.get("title", "")).strip()
            description = str(value.get("description", "")).strip()
            text = " ".join(part for part in (title, description) if part).strip()
        else:
            text = str(value).strip()
        if text:
            points.append(text)
    return points


def _summarize_note_data(note_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "titles": list(note_data.get("note_titles", []))[:5],
        "body": str(note_data.get("note_body", "")).strip(),
        "hashtags": list(note_data.get("hashtags", []))[:8],
        "selling_points": _normalize_selling_points(list(note_data.get("selling_points", []))),
        "sub_category": str(note_data.get("sub_category", "")).strip(),
    }


def _build_skipped_payload(llm_status: llm_content_service.LLMConfigStatus, reason: str) -> dict[str, Any]:
    return {
        "status": "SKIPPED",
        "reason": reason,
        "missing": list(llm_status.missing_fields),
        "invalid": list(llm_status.invalid_fields),
        "titles": [],
        "body": "",
        "hashtags": [],
        "selling_points": [],
    }


def evaluate_samples(
    samples: list[dict[str, str]] | None = None,
    only: str = "all",
) -> dict[str, Any]:
    sample_list = list(samples or DEFAULT_SAMPLES)
    llm_status = llm_content_service.get_llm_config_status("llm_openai_compatible")
    overall_llm_status = "ready" if llm_status.llm_config_ready else "skipped"
    payload: dict[str, Any] = {
        "version": APP_VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "llm_status": overall_llm_status,
        "llm_reason": None if llm_status.llm_config_ready else "LLM config incomplete",
        "llm_missing": list(llm_status.missing_fields),
        "llm_invalid": list(llm_status.invalid_fields),
        "llm_provider": llm_status.llm_provider,
        "llm_base_url": llm_status.llm_base_url_status,
        "llm_model": llm_status.llm_model_status,
        "llm_api_key_status": llm_status.llm_api_key_status,
        "mode": only,
        "samples": [],
    }

    for sample in sample_list:
        content_input = ContentGenerateInput(**sample)
        rule_based_result = generate_content_with_rule_based(content_input)
        rule_based_summary = _summarize_note_data(rule_based_result.note_data)
        sample_payload: dict[str, Any] = {
            "product_name": sample["product_name"],
            "category": sample["category"],
            "description": sample["description"],
            "content_type": sample["content_type"],
            "style": sample["style"],
            "rule_based": rule_based_summary,
            "llm": _build_skipped_payload(llm_status, "llm_config_incomplete"),
        }

        if only == "rule_based":
            sample_payload["llm"] = _build_skipped_payload(llm_status, "only_rule_based")
            payload["samples"].append(sample_payload)
            continue

        if not llm_status.llm_config_ready:
            payload["samples"].append(sample_payload)
            continue

        llm_result = llm_content_service.generate_openai_compatible_note_data(
            content_input=content_input,
            fallback_note_data=rule_based_result.note_data,
        )
        if llm_result.success:
            sample_payload["llm"] = {
                "status": "SUCCESS",
                "reason": None,
                "missing": [],
                "invalid": [],
                **_summarize_note_data(llm_result.note_data),
            }
        else:
            sample_payload["llm"] = {
                "status": "FAILED",
                "reason": llm_result.error_message or "llm_request_failed",
                "missing": [],
                "invalid": [],
                "titles": [],
                "body": "",
                "hashtags": [],
                "selling_points": [],
            }
        payload["samples"].append(sample_payload)

    return payload


def _sample_block_lines(title: str, sample_summary: dict[str, Any], body_label: str = "Body preview") -> list[str]:
    lines = [f"{title}:", "Titles:"]
    for item in sample_summary.get("titles", []):
        lines.append(f"- {item}")
    lines.extend([f"{body_label}:", sample_summary.get("body", "")])
    lines.extend(["Hashtags:", " ".join(sample_summary.get("hashtags", []))])
    lines.append("Selling points:")
    for item in sample_summary.get("selling_points", []):
        lines.append(f"- {item}")
    return lines


def render_text_report(payload: dict[str, Any]) -> str:
    lines = [
        "Batch Content Evaluation",
        "",
        f"Version: {payload['version']}",
        f"Samples: {len(payload['samples'])}",
        "Rule-based: enabled",
        f"LLM: {payload['llm_status']}",
        f"API Key: {payload['llm_api_key_status']} (masked)",
    ]
    if payload["llm_reason"]:
        lines.append(f"Reason: {payload['llm_reason']}")
    if payload["llm_missing"]:
        lines.append(f"Missing: {', '.join(payload['llm_missing'])}")
    if payload["llm_invalid"]:
        lines.append(f"Invalid: {', '.join(payload['llm_invalid'])}")
    lines.append("")

    for index, sample in enumerate(payload["samples"], start=1):
        lines.append(f"Sample {index}: {sample['product_name']}")
        lines.append(f"Category: {sample['category']}")
        sub_category = sample["rule_based"].get("sub_category")
        if sub_category:
            lines.append(f"Sub category: {sub_category}")
        if payload["mode"] != "llm":
            lines.extend(_sample_block_lines("Rule-based", sample["rule_based"]))
        llm_payload = sample["llm"]
        lines.append("LLM:")
        lines.append(f"Status: {llm_payload['status']}")
        if llm_payload["reason"]:
            lines.append(f"Reason: {REASON_LABELS.get(str(llm_payload['reason']), llm_payload['reason'])}")
        if llm_payload["missing"]:
            lines.append(f"Missing: {', '.join(llm_payload['missing'])}")
        if llm_payload["invalid"]:
            lines.append(f"Invalid: {', '.join(llm_payload['invalid'])}")
        if llm_payload["status"] == "SUCCESS":
            lines.extend(_sample_block_lines("LLM result", llm_payload))
        elif llm_payload["status"] == "SKIPPED" and payload["llm_status"] == "skipped":
            lines.append("No LLM requests were sent.")
        elif llm_payload["status"] == "FAILED":
            lines.append("Rule-based result is still available.")
        lines.append("")

    return "\n".join(lines).strip()


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Content Evaluation Report",
        "",
        f"- Version: {payload['version']}",
        f"- Generated at: {payload['generated_at']}",
        f"- LLM status: {payload['llm_status']}",
    ]
    if payload["llm_reason"]:
        lines.append(f"- Reason: {payload['llm_reason']}")
    if payload["llm_missing"]:
        lines.append(f"- Missing: {', '.join(payload['llm_missing'])}")
    lines.append("")

    for index, sample in enumerate(payload["samples"], start=1):
        lines.append(f"## {index}. {sample['product_name']}")
        lines.append("")
        lines.append("**Input**")
        lines.append("")
        lines.append(f"- Category: {sample['category']}")
        lines.append(f"- Description: {sample['description']}")
        lines.append(f"- Content type: {sample['content_type']}")
        lines.append(f"- Style: {sample['style']}")
        if payload["mode"] != "llm":
            lines.extend(
                [
                    "",
                    "**Rule-based**",
                    "",
                    "Titles:",
                    *[f"- {item}" for item in sample["rule_based"]["titles"]],
                    "",
                    "Body:",
                    sample["rule_based"]["body"],
                    "",
                    "Hashtags:",
                    " ".join(sample["rule_based"]["hashtags"]),
                    "",
                    "Selling points:",
                    *[f"- {item}" for item in sample["rule_based"]["selling_points"]],
                ]
            )
        llm_payload = sample["llm"]
        lines.extend(["", "**LLM**", "", f"- Status: {llm_payload['status']}"])
        if llm_payload["reason"]:
            lines.append(f"- Reason: {REASON_LABELS.get(str(llm_payload['reason']), llm_payload['reason'])}")
        if llm_payload["missing"]:
            lines.append(f"- Missing: {', '.join(llm_payload['missing'])}")
        if llm_payload["invalid"]:
            lines.append(f"- Invalid: {', '.join(llm_payload['invalid'])}")
        if llm_payload["status"] == "SUCCESS":
            lines.extend(
                [
                    "",
                    "Titles:",
                    *[f"- {item}" for item in llm_payload["titles"]],
                    "",
                    "Body:",
                    llm_payload["body"],
                    "",
                    "Hashtags:",
                    " ".join(llm_payload["hashtags"]),
                    "",
                    "Selling points:",
                    *[f"- {item}" for item in llm_payload["selling_points"]],
                ]
            )
        lines.append("")
    return "\n".join(lines).strip()


def _write_output(path: str, content: str) -> None:
    Path(path).write_text(content, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = evaluate_samples(only=args.only)

    if args.format == "json":
        rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    elif args.format == "markdown":
        rendered = render_markdown_report(payload)
    else:
        rendered = render_text_report(payload)
    print(rendered)

    if args.output:
        _write_output(args.output, rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
