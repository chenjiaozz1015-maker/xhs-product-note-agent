from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from app.config import FONTS_DIR, GENERATED_DIR, STATIC_DIR


PROJECT_CJK_FONT_PATHS = (
    FONTS_DIR / "NotoSansSC-Regular.otf",
    FONTS_DIR / "NotoSansCJK-Regular.ttc",
    FONTS_DIR / "SourceHanSansSC-Regular.otf",
)

LINUX_CJK_FONT_PATHS = (
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/noto/NotoSansSC-Regular.ttf"),
    Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"),
    Path("/usr/share/fonts/truetype/arphic/ukai.ttc"),
)

WINDOWS_CJK_FONT_PATHS = (
    Path("C:/Windows/Fonts/msyh.ttc"),
    Path("C:/Windows/Fonts/simhei.ttf"),
    Path("C:/Windows/Fonts/simsun.ttc"),
)

CJK_FONT_PATHS = PROJECT_CJK_FONT_PATHS + LINUX_CJK_FONT_PATHS + WINDOWS_CJK_FONT_PATHS
_FONT_STATUS_PRINTED = False


def get_cjk_font_path() -> Path | None:
    for font_path in CJK_FONT_PATHS:
        if not font_path.exists() or not font_path.is_file():
            continue
        try:
            ImageFont.truetype(str(font_path), 12)
            return font_path
        except OSError:
            continue
    return None


def load_font(size: int) -> ImageFont.ImageFont:
    global _FONT_STATUS_PRINTED

    font_path = get_cjk_font_path()
    if font_path:
        if not _FONT_STATUS_PRINTED:
            print(f"Using font: {font_path}")
            _FONT_STATUS_PRINTED = True
        return ImageFont.truetype(str(font_path), size)

    if not _FONT_STATUS_PRINTED:
        print("No CJK font found, Chinese text may render incorrectly.")
        _FONT_STATUS_PRINTED = True
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


def _fit_image(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    fitted = image.copy()
    fitted.thumbnail(size, Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", size, (255, 255, 255, 0))
    x = (size[0] - fitted.width) // 2
    y = (size[1] - fitted.height) // 2
    canvas.alpha_composite(fitted, (x, y))
    return canvas


def compose_posters(
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
    output_dir_path = Path(output_dir or GENERATED_DIR)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    src = _load_source_image(input_image_path)
    width, height = 1080, 1440

    font_cover_title = load_font(68)
    font_title = load_font(58)
    font_sub = load_font(36)
    font_small = load_font(30)
    font_card = load_font(38)
    font_card_small = load_font(32)

    short_title = (title or "种草机")[:18].replace("\n", " ")
    short_subtitle = (subtitle or "真实体验感 · 小红书发布素材")[:22].replace("\n", " ")
    point_texts = (selling_points or ["日常好用", "质感舒服", "适合轻分享"])[:3]
    while len(point_texts) < 3:
        point_texts.append("适合轻分享")
    summary_title_text = (summary_title or "适合日常轻分享")[:18].replace("\n", " ")
    suitable_for_text = (suitable_for or "喜欢轻分享的人")[:16].replace("\n", " ")
    recommend_reason_text = (recommend_reason or "好看、好用、日常容易带")[:18].replace("\n", " ")
    summary_sentence_text = (summary_sentence or "很值得试试")[:18].replace("\n", " ")

    cover_photo = _fit_image(src, (820, 720))
    cover = Image.new("RGBA", (width, height), (255, 247, 241, 255))
    cover_draw = ImageDraw.Draw(cover)
    cover_draw.rounded_rectangle((56, 60, 1024, 1370), radius=42, fill=(255, 255, 255, 238))
    cover_draw.rounded_rectangle((92, 108, 988, 890), radius=36, fill=(255, 239, 228, 255))
    cover_draw.rounded_rectangle((116, 126, 356, 186), radius=30, fill=(255, 112, 130, 255))
    cover.alpha_composite(cover_photo, (130, 150))
    cover_draw.rounded_rectangle((80, 910, 1000, 1338), radius=36, fill=(255, 255, 255, 252))
    cover_draw.rounded_rectangle((114, 964, 318, 1034), radius=28, fill=(255, 112, 130, 255))
    _draw_text(cover_draw, "好物推荐", (146, 138), font_small, (255, 255, 255, 255))
    _draw_text(cover_draw, "好物推荐", (146, 980), font_small, (255, 255, 255, 255))
    _draw_text(cover_draw, short_title, (116, 1070), font_cover_title, (38, 38, 38, 255))
    _draw_text(cover_draw, short_subtitle, (118, 1180), font_sub, (105, 82, 70, 255))
    _draw_text(cover_draw, "封面图 / 配图 / 文案一次生成", (118, 1250), font_small, (142, 110, 96, 255))

    points_photo = _fit_image(src, (820, 500))
    points = Image.new("RGBA", (width, height), (250, 247, 240, 255))
    points_draw = ImageDraw.Draw(points)
    points_draw.rounded_rectangle((48, 48, 1032, 1392), radius=42, fill=(255, 255, 255, 246))
    points_draw.rounded_rectangle((88, 92, 992, 650), radius=34, fill=(255, 241, 230, 255))
    points.alpha_composite(points_photo, (130, 122))
    points_draw.rounded_rectangle((92, 690, 988, 780), radius=32, fill=(255, 226, 211, 255))
    _draw_text(points_draw, "我喜欢它的 3 个点", (126, 708), font_title, (42, 42, 42, 255))

    point_cards = [
        ((116, 830, 964, 970), "01", point_texts[0][:18]),
        ((116, 1005, 964, 1145), "02", point_texts[1][:18]),
        ((116, 1180, 964, 1320), "03", point_texts[2][:18]),
    ]
    for box, number, text in point_cards:
        points_draw.rounded_rectangle(box, radius=26, fill=(255, 255, 255, 255), outline=(242, 223, 211, 255), width=2)
        points_draw.ellipse((box[0] + 30, box[1] + 38, box[0] + 94, box[1] + 102), fill=(255, 112, 130, 255))
        _draw_text(points_draw, number, (box[0] + 45, box[1] + 50), font_small, (255, 255, 255, 255))
        _draw_text(points_draw, text, (box[0] + 124, box[1] + 48), font_card, (66, 66, 66, 255))

    summary_photo = _fit_image(src, (560, 520))
    summary = Image.new("RGBA", (width, height), (248, 248, 245, 255))
    summary_draw = ImageDraw.Draw(summary)
    summary_draw.rounded_rectangle((48, 48, 1032, 1392), radius=42, fill=(255, 255, 255, 244))
    summary_draw.rounded_rectangle((88, 88, 992, 210), radius=34, fill=(255, 225, 205, 255))
    _draw_text(summary_draw, "最后想说", (128, 112), font_sub, (120, 90, 70, 255))
    _draw_text(summary_draw, summary_title_text, (128, 250), font_title, (42, 42, 42, 255))
    summary_draw.rounded_rectangle((250, 340, 830, 900), radius=34, fill=(255, 243, 232, 255))
    summary.alpha_composite(summary_photo, (260, 360))

    summary_cards = [
        ((92, 945, 988, 1065), "适合谁", suitable_for_text),
        ((92, 1090, 988, 1210), "推荐理由", recommend_reason_text),
        ((92, 1235, 988, 1355), "一句话总结", summary_sentence_text),
    ]
    for box, label, text in summary_cards:
        summary_draw.rounded_rectangle(box, radius=24, fill=(248, 246, 238, 255), outline=(234, 226, 214, 255), width=2)
        _draw_text(summary_draw, label, (box[0] + 34, box[1] + 24), font_card_small, (145, 105, 82, 255))
        _draw_text(summary_draw, text, (box[0] + 230, box[1] + 24), font_card, (60, 60, 60, 255))

    variants = [cover, points, summary]
    paths = []
    source_stem = Path(input_image_path).stem or "sample"
    for idx, variant in enumerate(variants, start=1):
        suffix = ["cover", "points", "summary"][idx - 1]
        out_path = output_dir_path / f"poster_{idx}_{source_stem}_{suffix}.png"
        variant.save(out_path)
        paths.append(f"/static/generated/{out_path.name}")
    return paths
