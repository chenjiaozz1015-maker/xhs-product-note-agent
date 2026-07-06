from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.config import POSTER_ENGINE_TYPE
from app.services.image_composer import compose_posters_enhanced


CANVAS_SIZE = (1080, 1440)
SUPPORTED_ENGINE_TYPES = {"pillow", "external_placeholder"}


@dataclass(frozen=True)
class PosterRenderInput:
    """Unified poster render input for all current and future engines."""

    product_image_path: str
    output_dir: str | None = None
    product_name: str = ""
    category: str = "其他好物"
    content_type: str = ""
    style: str = "清新简约"
    note_data: dict[str, Any] = field(default_factory=dict)
    canvas_width: int = CANVAS_SIZE[0]
    canvas_height: int = CANVAS_SIZE[1]
    image_count: int = 3


@dataclass(frozen=True)
class PosterRenderResult:
    """Unified poster render result for all engines."""

    success: bool
    image_paths: list[str] = field(default_factory=list)
    engine_type: str = "pillow"
    error_message: str | None = None


def resolve_engine_type(engine_type: str | None = None) -> str:
    resolved = str(engine_type or POSTER_ENGINE_TYPE or "pillow").strip() or "pillow"
    if resolved in SUPPORTED_ENGINE_TYPES:
        return resolved
    return "pillow"


def render_posters_with_pillow(render_input: PosterRenderInput) -> PosterRenderResult:
    note_data = render_input.note_data
    image_paths = compose_posters_enhanced(
        input_image_path=render_input.product_image_path,
        output_dir=render_input.output_dir,
        title=str(note_data.get("cover_title", "种草机")),
        subtitle=str(note_data.get("cover_subtitle", "")),
        style=render_input.style,
        selling_points=list(note_data.get("selling_points") or []),
        summary_title=str(note_data.get("summary_title", "")),
        suitable_for=str(note_data.get("suitable_for", "")),
        recommend_reason=str(note_data.get("recommend_reason", "")),
        summary_sentence=str(note_data.get("summary_sentence", "")),
        category=render_input.category,
        content_type=render_input.content_type,
        product_name=render_input.product_name,
    )
    return PosterRenderResult(success=True, image_paths=image_paths, engine_type="pillow")


def render_posters(
    render_input: PosterRenderInput,
    engine_type: str | None = None,
) -> PosterRenderResult:
    resolved_engine_type = resolve_engine_type(engine_type)

    if resolved_engine_type == "external_placeholder":
        pillow_result = render_posters_with_pillow(render_input)
        return PosterRenderResult(
            success=pillow_result.success,
            image_paths=pillow_result.image_paths,
            engine_type="pillow",
            error_message="external_placeholder 暂未接入，已自动回退到 pillow 引擎。",
        )

    return render_posters_with_pillow(render_input)


def generate_posters(
    input_image_path: str,
    output_dir: str | None = None,
    title: str = "种草机",
    subtitle: str = "",
    style: str = "清新简约",
    selling_points: list[str] | None = None,
    summary_title: str = "",
    suitable_for: str = "",
    recommend_reason: str = "",
    summary_sentence: str = "",
) -> list[str]:
    """Backward-compatible helper used by legacy tests and route code."""
    result = render_posters(
        PosterRenderInput(
            product_image_path=input_image_path,
            output_dir=output_dir,
            product_name=title,
            style=style,
            note_data={
                "cover_title": title,
                "cover_subtitle": subtitle,
                "selling_points": selling_points or [],
                "summary_title": summary_title,
                "suitable_for": suitable_for,
                "recommend_reason": recommend_reason,
                "summary_sentence": summary_sentence,
            },
        )
    )
    return result.image_paths
