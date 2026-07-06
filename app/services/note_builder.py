from app.services.content_engine_adapter import ContentGenerateInput, generate_content


def _build_content_engine_meta(result) -> dict:
    engine_type = result.engine_type or "rule_based"
    requested_engine_type = result.requested_engine_type or engine_type
    fallback_used = bool(result.fallback_used)
    fallback_reason = result.fallback_reason or ""

    if engine_type == "llm_openai_compatible":
        display = "LLM 生成"
    elif fallback_used and requested_engine_type == "llm_openai_compatible":
        display = "规则引擎（LLM 不可用，已自动回退）"
    else:
        display = "规则引擎"

    return {
        "content_engine_type": engine_type,
        "content_engine_requested_type": requested_engine_type,
        "content_engine_fallback_used": fallback_used,
        "content_engine_fallback_reason": fallback_reason,
        "content_engine_display": display,
    }


def build_result_payload(
    description: str,
    content_type: str,
    style: str,
    image_paths: list[str],
    product_name: str = "",
    category: str = "其他好物",
) -> dict:
    result = generate_content(
        ContentGenerateInput(
            product_name=product_name,
            category=category,
            description=description,
            content_type=content_type,
            style=style,
        )
    )
    payload = dict(result.note_data)
    payload["image_paths"] = image_paths
    payload.update(_build_content_engine_meta(result))
    if result.error_message:
        payload["content_engine_warning"] = result.error_message
    return payload
