from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.image_composer import compose_posters


CANVAS_SIZE = (1080, 1440)


@dataclass(frozen=True)
class PosterRenderInput:
    """Poster engine boundary.

    The app currently renders with the local Pillow composer. This input object
    keeps the handoff explicit so a future GitHub/open-source poster engine can
    be adapted here without changing upload, result, download, or copy flows.
    """

    input_image_path: str
    output_dir: str | None = None
    canvas_size: tuple[int, int] = CANVAS_SIZE
    note_data: dict[str, Any] = field(default_factory=dict)
    style: str = "清新简约"
    category: str = "其他好物"
    product_name: str = ""


def render_posters_with_default_engine(render_input: PosterRenderInput) -> list[str]:
    """Render posters with the built-in lightweight Pillow engine."""
    note_data = render_input.note_data
    return compose_posters(
        input_image_path=render_input.input_image_path,
        output_dir=render_input.output_dir,
        title=str(note_data.get("cover_title", "种草机")),
        subtitle=str(note_data.get("cover_subtitle", "")),
        style=render_input.style,
        selling_points=list(note_data.get("selling_points") or []),
        summary_title=str(note_data.get("summary_title", "")),
        suitable_for=str(note_data.get("suitable_for", "")),
        recommend_reason=str(note_data.get("recommend_reason", "")),
        summary_sentence=str(note_data.get("summary_sentence", "")),
    )


def render_posters(render_input: PosterRenderInput) -> list[str]:
    """Adapter entry point reserved for future third-party poster engines."""
    return render_posters_with_default_engine(render_input)


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
    """Backward-compatible helper used by the current generate route."""
    return render_posters(
        PosterRenderInput(
            input_image_path=input_image_path,
            output_dir=output_dir,
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
