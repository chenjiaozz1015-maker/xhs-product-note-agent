from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from app.config import GENERATED_DIR, STATIC_DIR


def _load_source_image(input_image_path: str) -> Image.Image:
    source_path = Path(input_image_path)
    if source_path.exists() and source_path.is_file():
        return Image.open(source_path).convert("RGBA")

    placeholder_path = STATIC_DIR / "template_assets" / "placeholder.png"
    if not placeholder_path.exists():
        placeholder = Image.new("RGBA", (1080, 1440), (248, 240, 225, 255))
        placeholder.save(placeholder_path)
    return Image.open(placeholder_path).convert("RGBA")


def compose_posters(input_image_path: str, output_dir: str | None = None, title: str = "种草机") -> list[str]:
    output_dir_path = Path(output_dir or GENERATED_DIR)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    src = _load_source_image(input_image_path)
    src = src.resize((720, 960))

    width, height = 1080, 1440
    base = Image.new("RGBA", (width, height), (255, 255, 255, 255))

    x = (width - src.width) // 2
    y = 80
    base.alpha_composite(src, (x, y))

    draw = ImageDraw.Draw(base)
    try:
        font_title = ImageFont.truetype("arial.ttf", 46)
        font_sub = ImageFont.truetype("arial.ttf", 28)
        font_small = ImageFont.truetype("arial.ttf", 24)
    except OSError:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.rounded_rectangle((60, 1080, 1020, 1370), radius=28, fill=(255, 255, 255, 240))
    draw.text((90, 1100), title[:22], fill=(40, 40, 40, 255), font=font_title)
    draw.text((90, 1160), "小红书风格种草图", fill=(120, 120, 120, 255), font=font_sub)
    draw.text((90, 1210), "模板化合成 • 轻量版", fill=(120, 120, 120, 255), font=font_small)

    paths = []
    source_stem = Path(input_image_path).stem or "sample"
    for idx, suffix in enumerate(["cover", "points", "summary"], start=1):
        out_path = output_dir_path / f"poster_{idx}_{source_stem}_{suffix}.png"
        base.save(out_path)
        paths.append(f"/static/generated/{out_path.name}")
    return paths
