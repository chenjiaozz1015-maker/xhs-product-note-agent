from app.services.content_generator import generate_note_payload


def build_result_payload(description: str, content_type: str, style: str, image_paths: list[str]) -> dict:
    payload = generate_note_payload(description, content_type, style)
    payload["image_paths"] = image_paths
    return payload
