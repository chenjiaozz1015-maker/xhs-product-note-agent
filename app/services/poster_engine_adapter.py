from app.services.image_composer import compose_posters


def generate_posters(
    input_image_path: str,
    output_dir: str | None = None,
    title: str = "种草机",
    subtitle: str = "",
    selling_points: list[str] | None = None,
    summary_title: str = "",
    suitable_for: str = "",
    recommend_reason: str = "",
    summary_sentence: str = "",
) -> list[str]:
    """适配层占位：当前先复用本地模板合成逻辑。"""
    return compose_posters(
        input_image_path=input_image_path,
        output_dir=output_dir,
        title=title,
        subtitle=subtitle,
        selling_points=selling_points,
        summary_title=summary_title,
        suitable_for=suitable_for,
        recommend_reason=recommend_reason,
        summary_sentence=summary_sentence,
    )
