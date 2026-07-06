from app.services.content_engine_adapter import ContentGenerateInput, generate_content


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
    if result.error_message:
        payload["content_engine_warning"] = result.error_message
    return payload
