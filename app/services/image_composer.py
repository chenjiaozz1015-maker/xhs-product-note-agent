from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from app.config import GENERATED_DIR, STATIC_DIR


WINDOWS_CHINESE_FONT_PATHS = (
    Path("C:/Windows/Fonts/msyh.ttc"),
    Path("C:/Windows/Fonts/simhei.ttf"),
    Path("C:/Windows/Fonts/simsun.ttc"),
)


def load_font(size: int) -> ImageFont.ImageFont:
    for font_path in WINDOWS_CHINESE_FONT_PATHS:
        if not font_path.exists():
            continue
        try:
            return ImageFont.truetype(str(font_path), size)
        except OSError:
            continue
    return ImageFont.load_default()


def _load_source_image(input_image_path: str) -> Image.Image:
    source_path = Path(input_image_path)
    if source_path.exists() and source_path.is_file():
        return Image.open(source_path).convert("RGBA")

    placeholder_path = STATIC_DIR / "template_assets" / "placeholder.png"
    if not placeholder_path.exists():
        placeholder = Image.new("RGBA", (1080, 1440), (248, 240, 225, 255))
        placeholder.save(placeholder_path)
    return Image.open(placeholder_path).convert("RGBA")


def _draw_text(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], font: ImageFont.ImageFont, fill: tuple[int, int, int, int], anchor: str = "lt") -> None:
    draw.text(xy, text, font=font, fill=fill, anchor=anchor)


def compose_posters(input_image_path: str, output_dir: str | None = None, title: str = "种草机") -> list[str]:
    output_dir_path = Path(output_dir or GENERATED_DIR)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    src = _load_source_image(input_image_path)
    width, height = 1080, 1440
    photo = src.resize((760, 760))

    font_title = load_font(54)
    font_sub = load_font(30)
    font_small = load_font(24)
    font_card = load_font(26)

    short_title = (title or "种草机")[:18].replace("\n", " ")

    cover = Image.new("RGBA", (width, height), (255, 248, 240, 255))
    cover_draw = ImageDraw.Draw(cover)
    cover_draw.rounded_rectangle((70, 70, 1010, 1320), radius=32, fill=(255, 255, 255, 210))
    cover_draw.rounded_rectangle((90, 90, 990, 1300), radius=28, outline=(244, 215, 193, 255), width=3)
    cover_draw.rounded_rectangle((90, 1020, 270, 1120), radius=18, fill=(255, 176, 144, 255))
    cover.alpha_composite(photo, (150, 220))
    _draw_text(cover_draw, "好物推荐", (110, 1035), font_small, (255, 255, 255, 255))
    _draw_text(cover_draw, short_title, (100, 1120), font_title, (50, 50, 50, 255))
    _draw_text(cover_draw, "轻分享｜真实体验｜小红书风格", (100, 1210), font_sub, (113, 113, 113, 255))

    points = Image.new("RGBA", (width, height), (250, 247, 240, 255))
    points_draw = ImageDraw.Draw(points)
    points_draw.rounded_rectangle((40, 40, 1040, 1400), radius=34, fill=(255, 255, 255, 245))
    points_draw.rounded_rectangle((90, 90, 1000, 1160), radius=24, fill=(255, 243, 232, 255))
    points.alpha_composite(photo.resize((620, 420)), (110, 140))
    _draw_text(points_draw, "我喜欢它的 3 个点", (120, 600), font_title, (50, 50, 50, 255))
    points_draw.rounded_rectangle((120, 680, 960, 810), radius=18, fill=(255, 255, 255, 255))
    points_draw.rounded_rectangle((120, 850, 960, 980), radius=18, fill=(255, 255, 255, 255))
    points_draw.rounded_rectangle((120, 1020, 960, 1150), radius=18, fill=(255, 255, 255, 255))
    _draw_text(points_draw, "• 日常好用", (150, 710), font_card, (90, 90, 90, 255))
    _draw_text(points_draw, "• 质感舒服", (150, 880), font_card, (90, 90, 90, 255))
    _draw_text(points_draw, "• 适合轻分享", (150, 1050), font_card, (90, 90, 90, 255))

    summary = Image.new("RGBA", (width, height), (248, 248, 245, 255))
    summary_draw = ImageDraw.Draw(summary)
    summary_draw.rounded_rectangle((40, 40, 1040, 1400), radius=34, fill=(255, 255, 255, 240))
    summary_draw.rounded_rectangle((80, 80, 1000, 180), radius=20, fill=(255, 225, 205, 255))
    _draw_text(summary_draw, "最后想说", (120, 100), font_sub, (120, 90, 70, 255))
    _draw_text(summary_draw, "适合日常轻分享", (120, 230), font_title, (50, 50, 50, 255))
    summary.alpha_composite(photo.resize((420, 420)), (160, 310))
    summary_draw.rounded_rectangle((90, 790, 990, 1320), radius=24, fill=(248, 246, 238, 255))
    _draw_text(summary_draw, "适合：喜欢轻分享的人", (120, 830), font_card, (70, 70, 70, 255))
    _draw_text(summary_draw, "推荐理由：好看、好用、日常容易带", (120, 900), font_card, (70, 70, 70, 255))
    _draw_text(summary_draw, "一句话：很值得试试", (120, 970), font_card, (70, 70, 70, 255))

    variants = [cover, points, summary]
    paths = []
    source_stem = Path(input_image_path).stem or "sample"
    for idx, variant in enumerate(variants, start=1):
        suffix = ["cover", "points", "summary"][idx - 1]
        out_path = output_dir_path / f"poster_{idx}_{source_stem}_{suffix}.png"
        variant.save(out_path)
        paths.append(f"/static/generated/{out_path.name}")
    return paths
