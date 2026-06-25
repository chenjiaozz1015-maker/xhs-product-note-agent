from app.services.image_composer import compose_posters


def generate_posters(input_image_path: str, output_dir: str | None = None, title: str = "种草机") -> list[str]:
    """适配层占位：当前先复用本地模板合成逻辑。"""
    return compose_posters(input_image_path=input_image_path, output_dir=output_dir, title=title)
