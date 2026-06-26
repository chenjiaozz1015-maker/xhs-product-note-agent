from app.services.content_generator import generate_note_payload


def build_result_payload(
    description: str,
    content_type: str,
    style: str,
    image_paths: list[str],
    product_name: str = "",
    category: str = "其他好物",
) -> dict:
    payload = generate_note_payload(description, content_type, style, product_name=product_name, category=category)
    payload["image_paths"] = image_paths
    return payload
