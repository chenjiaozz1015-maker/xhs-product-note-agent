from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.config import CONTENT_ENGINE_TYPE
from app.services.content_generator import generate_note_payload
from app.services.llm_content_service import generate_openai_compatible_note_data


SUPPORTED_CONTENT_ENGINE_TYPES = {
    "rule_based",
    "llm_placeholder",
    "llm_openai_compatible",
}


@dataclass(frozen=True)
class ContentGenerateInput:
    product_name: str = ""
    category: str = "其他好物"
    description: str = ""
    content_type: str = "好物推荐"
    style: str = "清新简约"
    category_profile: dict[str, Any] | None = None
    extra_context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ContentGenerateResult:
    success: bool
    engine_type: str = "rule_based"
    note_data: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None


def resolve_content_engine_type(engine_type: str | None = None) -> str:
    resolved = str(engine_type or CONTENT_ENGINE_TYPE or "rule_based").strip() or "rule_based"
    if resolved in SUPPORTED_CONTENT_ENGINE_TYPES:
        return resolved
    return "rule_based"


def generate_content_with_rule_based(content_input: ContentGenerateInput) -> ContentGenerateResult:
    note_data = generate_note_payload(
        description=content_input.description,
        content_type=content_input.content_type,
        style=content_input.style,
        product_name=content_input.product_name,
        category=content_input.category,
    )
    return ContentGenerateResult(success=True, engine_type="rule_based", note_data=note_data)


def generate_content_with_llm_openai_compatible(
    content_input: ContentGenerateInput,
    fallback_note_data: dict[str, Any],
) -> ContentGenerateResult:
    llm_result = generate_openai_compatible_note_data(content_input, fallback_note_data=fallback_note_data)
    if llm_result.success:
        return ContentGenerateResult(
            success=True,
            engine_type="llm_openai_compatible",
            note_data=llm_result.note_data,
            error_message=llm_result.error_message,
        )
    return ContentGenerateResult(
        success=True,
        engine_type="rule_based",
        note_data=fallback_note_data,
        error_message=llm_result.error_message,
    )


def generate_content(
    content_input: ContentGenerateInput,
    engine_type: str | None = None,
) -> ContentGenerateResult:
    resolved_engine_type = resolve_content_engine_type(engine_type)
    rule_based_result = generate_content_with_rule_based(content_input)

    if resolved_engine_type == "llm_placeholder":
        return ContentGenerateResult(
            success=rule_based_result.success,
            engine_type="rule_based",
            note_data=rule_based_result.note_data,
            error_message="llm_placeholder 当前未接入真实大模型，已 fallback 到 rule_based。",
        )

    if resolved_engine_type == "llm_openai_compatible":
        return generate_content_with_llm_openai_compatible(content_input, rule_based_result.note_data)

    return rule_based_result
