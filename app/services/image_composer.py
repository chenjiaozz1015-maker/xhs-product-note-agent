from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.config import FONTS_DIR, GENERATED_DIR, STATIC_DIR
from app.services.category_profile import (
    GENERAL_SUBCATEGORY,
    MAIN_CATEGORY_LABELS,
    ProductProfile,
    detect_product_profile,
    get_profile_copy,
)


PROJECT_CJK_FONT_PATHS = (
    FONTS_DIR / "NotoSansSC-Regular.ttf",
    FONTS_DIR / "NotoSansSC-Regular.otf",
    FONTS_DIR / "NotoSansCJK-Regular.ttc",
    FONTS_DIR / "SourceHanSansSC-Regular.otf",
)
LINUX_CJK_FONT_PATHS = (
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/noto/NotoSansSC-Regular.ttf"),
)
WINDOWS_CJK_FONT_PATHS = (
    Path("C:/Windows/Fonts/msyh.ttc"),
    Path("C:/Windows/Fonts/simhei.ttf"),
)
CJK_FONT_PATHS = PROJECT_CJK_FONT_PATHS + LINUX_CJK_FONT_PATHS + WINDOWS_CJK_FONT_PATHS

STYLE_THEMES = {
    "清新简约": {
        "background": (248, 250, 248, 255),
        "card": (255, 255, 255, 248),
        "photo_bg": (239, 247, 241, 255),
        "accent": (91, 158, 132, 255),
        "accent_soft": (222, 242, 232, 255),
        "text": (39, 48, 44, 255),
        "muted": (98, 120, 110, 255),
        "border": (218, 232, 224, 255),
        "radius": 28,
        "decoration": "minimal",
        "point_label": "dot",
        "summary_marker": "label",
        "cover_badge": "真实分享",
        "cover_note": "留白更舒服，标题更清楚",
    },
    "可爱手账": {
        "background": (255, 246, 239, 255),
        "card": (255, 255, 255, 248),
        "photo_bg": (255, 235, 225, 255),
        "accent": (255, 125, 148, 255),
        "accent_soft": (255, 230, 236, 255),
        "text": (64, 48, 47, 255),
        "muted": (151, 96, 92, 255),
        "border": (248, 209, 199, 255),
        "radius": 36,
        "decoration": "stickers",
        "point_label": "sticker",
        "summary_marker": "sticker",
        "cover_badge": "今日好物",
        "cover_note": "贴纸感更轻一点，商品更清楚",
    },
    "生活方式": {
        "background": (246, 242, 235, 255),
        "card": (255, 254, 250, 248),
        "photo_bg": (236, 229, 219, 255),
        "accent": (142, 113, 82, 255),
        "accent_soft": (235, 222, 204, 255),
        "text": (45, 41, 36, 255),
        "muted": (116, 105, 92, 255),
        "border": (224, 214, 200, 255),
        "radius": 24,
        "decoration": "magazine",
        "point_label": "line",
        "summary_marker": "label",
        "cover_badge": "生活方式",
        "cover_note": "更像日常场景里的杂志标题",
    },
    "干货清单": {
        "background": (247, 249, 246, 255),
        "card": (255, 255, 255, 248),
        "photo_bg": (237, 244, 237, 255),
        "accent": (69, 132, 105, 255),
        "accent_soft": (224, 240, 229, 255),
        "text": (34, 45, 40, 255),
        "muted": (78, 105, 94, 255),
        "border": (194, 218, 204, 255),
        "radius": 20,
        "decoration": "checklist",
        "point_label": "number",
        "summary_marker": "check",
        "cover_badge": "清单分享",
        "cover_note": "01 02 03 更适合直接看重点",
    },
    "温柔日常": {
        "background": (255, 248, 241, 255),
        "card": (255, 253, 249, 248),
        "photo_bg": (255, 239, 229, 255),
        "accent": (224, 143, 132, 255),
        "accent_soft": (255, 232, 226, 255),
        "text": (64, 50, 45, 255),
        "muted": (132, 97, 88, 255),
        "border": (244, 215, 204, 255),
        "radius": 34,
        "decoration": "soft",
        "point_label": "soft",
        "summary_marker": "soft",
        "cover_badge": "温柔日常",
        "cover_note": "奶油色更柔和，适合日常分享",
    },
}


_FONT_STATUS_PRINTED = False


def get_style_theme(style: str) -> dict:
    return STYLE_THEMES.get(style, STYLE_THEMES["清新简约"]).copy()


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


def _fit_image(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    fitted = image.copy()
    fitted.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, (255, 255, 255, 0))
    x = (size[0] - fitted.width) // 2
    y = (size[1] - fitted.height) // 2
    canvas.alpha_composite(fitted, (x, y))
    return canvas


def _draw_text(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], font: ImageFont.ImageFont, fill: tuple[int, int, int, int]) -> None:
    draw.text(xy, text, font=font, fill=fill)


def _draw_pill(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], font: ImageFont.ImageFont, fill: tuple[int, int, int, int], text_fill: tuple[int, int, int, int], outline: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    width = (bbox[2] - bbox[0]) + 36
    height = (bbox[3] - bbox[1]) + 20
    rect = (xy[0], xy[1], xy[0] + width, xy[1] + height)
    draw.rounded_rectangle(rect, radius=max(16, height // 2), fill=fill, outline=outline, width=2)
    draw.text((xy[0] + 18, xy[1] + 8), text, font=font, fill=text_fill)
    return rect


def _clip_text(text: str, limit: int, fallback: str) -> str:
    value = (text or "").replace("\n", " ").strip()
    return (value or fallback)[:limit]


def _wrap_text(text: str, line_length: int, max_lines: int = 2) -> list[str]:
    content = (text or "").replace("\n", " ").strip()
    if not content:
        return []
    lines: list[str] = []
    remaining = content
    while remaining and len(lines) < max_lines:
        if len(remaining) <= line_length:
            lines.append(remaining)
            break
        lines.append(remaining[:line_length])
        remaining = remaining[line_length:]
    if remaining and len(lines) == max_lines:
        lines[-1] = lines[-1][: max(0, line_length - 1)] + "…"
    return lines


def _profile_from_visual_inputs(category: str, product_name: str, description: str) -> ProductProfile:
    return detect_product_profile(product_name, category, description)


def _resolve_product_context(category: str, product_name: str, description: str) -> str:
    return _profile_from_visual_inputs(category, product_name, description).sub_category


def _default_profile_for_category(category: str) -> ProductProfile:
    main_category = next((key for key, label in MAIN_CATEGORY_LABELS.items() if label == category), "other")
    sub_category = GENERAL_SUBCATEGORY.get(main_category, "general")
    copy_config = get_profile_copy(
        ProductProfile(main_category=main_category, sub_category=sub_category, category_label=MAIN_CATEGORY_LABELS[main_category], keywords=(), tone_tags=())
    )
    return ProductProfile(
        main_category=main_category,
        sub_category=sub_category,
        category_label=MAIN_CATEGORY_LABELS[main_category],
        keywords=(),
        tone_tags=tuple(copy_config.get("tone_tags", [])),
    )


def _copy_from_context(category: str, product_context: str = "default") -> dict:
    if product_context != "default":
        main_category = next((key for key, label in MAIN_CATEGORY_LABELS.items() if label == category), "other")
        profile = ProductProfile(
            main_category=main_category,
            sub_category=product_context,
            category_label=category or MAIN_CATEGORY_LABELS[main_category],
            keywords=(),
            tone_tags=(),
        )
        return get_profile_copy(profile)
    return get_profile_copy(_default_profile_for_category(category))


def _category_tags(category: str, content_type: str, product_context: str = "default") -> list[str]:
    return list(_copy_from_context(category, product_context).get("tone_tags", ["真实分享", "日常好物", "轻松种草"]))[:3]


def _point_detail_text(category: str, index: int, product_context: str = "default") -> str:
    values = list(_copy_from_context(category, product_context).get("point_details", ["更适合放进日常场景", "一眼看懂推荐重点", "适合直接做真实分享"]))
    return values[min(index, len(values) - 1)]


def _summary_label_text(category: str, product_context: str = "default") -> list[str]:
    values = list(_copy_from_context(category, product_context).get("summary_labels", ["适合场景", "推荐理由", "一眼看懂"]))
    if len(values) < 3:
        values.extend(["适合场景", "推荐理由", "一眼看懂"][len(values):3])
    return values[:3]


def _get_style_layout(decoration: str) -> dict:
    layouts = {
        "minimal": {
            "cover_photo_box": (86, 110, 994, 828),
            "cover_photo_size": (820, 660),
            "cover_text_box": (86, 878, 994, 1332),
            "point_photo_box": (120, 110, 960, 560),
            "point_photo_size": (720, 360),
            "point_cards": [((118, 760, 962, 902), "01"), ((118, 944, 962, 1086), "02"), ((118, 1128, 962, 1270), "03")],
            "summary_photo_box": (228, 300, 852, 860),
            "summary_photo_size": (540, 420),
        },
        "stickers": {
            "cover_photo_box": (120, 170, 960, 820),
            "cover_photo_size": (720, 540),
            "cover_text_box": (86, 875, 994, 1336),
            "point_photo_box": (132, 120, 948, 530),
            "point_photo_size": (680, 320),
            "point_cards": [((102, 748, 978, 892), "01"), ((124, 930, 954, 1078), "02"), ((104, 1114, 972, 1262), "03")],
            "summary_photo_box": (250, 320, 830, 840),
            "summary_photo_size": (500, 390),
        },
        "magazine": {
            "cover_photo_box": (74, 96, 1006, 920),
            "cover_photo_size": (860, 730),
            "cover_text_box": (90, 952, 990, 1328),
            "point_photo_box": (86, 92, 992, 700),
            "point_photo_size": (840, 520),
            "point_cards": [((96, 780, 984, 918), "01"), ((96, 958, 984, 1096), "02"), ((96, 1136, 984, 1274), "03")],
            "summary_photo_box": (100, 320, 980, 860),
            "summary_photo_size": (800, 460),
        },
        "checklist": {
            "cover_photo_box": (116, 280, 964, 850),
            "cover_photo_size": (760, 460),
            "cover_text_box": (86, 90, 994, 246),
            "point_photo_box": (110, 100, 970, 470),
            "point_photo_size": (760, 280),
            "point_cards": [((92, 724, 988, 870), "01"), ((92, 910, 988, 1056), "02"), ((92, 1096, 988, 1242), "03")],
            "summary_photo_box": (120, 290, 960, 700),
            "summary_photo_size": (740, 320),
        },
        "soft": {
            "cover_photo_box": (110, 220, 970, 850),
            "cover_photo_size": (780, 540),
            "cover_text_box": (92, 104, 988, 236),
            "point_photo_box": (126, 116, 954, 560),
            "point_photo_size": (720, 360),
            "point_cards": [((126, 756, 954, 900), "01"), ((118, 944, 962, 1092), "02"), ((126, 1132, 954, 1276), "03")],
            "summary_photo_box": (230, 310, 850, 830),
            "summary_photo_size": (560, 420),
        },
    }
    return layouts.get(decoration, layouts["minimal"])


def _box_centered_position(box: tuple[int, int, int, int], image: Image.Image) -> tuple[int, int]:
    return (box[0] + (box[2] - box[0] - image.width) // 2, box[1] + (box[3] - box[1] - image.height) // 2)


def _prepare_cover_photo(src: Image.Image, theme: dict, size: tuple[int, int]) -> Image.Image:
    photo = _fit_image(src, size)
    if theme["decoration"] == "stickers":
        return photo.rotate(-2, resample=Image.Resampling.BICUBIC, expand=True)
    return photo


def _render_variants(
    input_image_path: str,
    output_dir: str | None,
    title: str,
    subtitle: str,
    style: str,
    selling_points: list[str] | None,
    summary_title: str,
    suitable_for: str,
    recommend_reason: str,
    summary_sentence: str,
    category: str,
    content_type: str,
    product_name: str,
    enlarge: bool,
) -> list[str]:
    output_dir_path = Path(output_dir or GENERATED_DIR)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    src = _load_source_image(input_image_path)
    width, height = 1080, 1440
    theme = get_style_theme(style)
    layout = _get_style_layout(theme["decoration"])
    product_context = _resolve_product_context(category, product_name, f"{title} {subtitle}")
    cover_tags = _category_tags(category, content_type, product_context)
    summary_labels = _summary_label_text(category, product_context)

    font_cover = load_font(72)
    font_title = load_font(50)
    font_sub = load_font(32)
    font_small = load_font(26)
    font_tiny = load_font(22)
    title_lines = _wrap_text(_clip_text(title, 22, "种草机"), 10, 2)
    subtitle_text = _clip_text(subtitle, 28, "真实分享的小红书素材")
    points = list(selling_points or ["日常好用", "质感舒服", "适合轻分享"])[:3]
    while len(points) < 3:
        points.append("适合轻分享")

    cover_photo = _prepare_cover_photo(src, theme, layout["cover_photo_size"])
    cover = Image.new("RGBA", (width, height), theme["background"])
    cover_draw = ImageDraw.Draw(cover)
    cover_draw.rounded_rectangle((54, 60, 1026, 1378), radius=theme["radius"] + 8, fill=theme["card"])
    cover_draw.rounded_rectangle(layout["cover_photo_box"], radius=theme["radius"], fill=theme["photo_bg"], outline=theme["border"], width=2)
    cover.alpha_composite(cover_photo, _box_centered_position(layout["cover_photo_box"], cover_photo))
    cover_draw.rounded_rectangle(layout["cover_text_box"], radius=theme["radius"], fill=(255, 255, 255, 250), outline=theme["border"], width=2)
    _draw_pill(cover_draw, theme["cover_badge"], (112, 112), font_tiny, theme["accent"], (255, 255, 255, 255), theme["accent"])
    y = layout["cover_text_box"][1] + 44
    for line in title_lines:
        _draw_text(cover_draw, line, (122, y), font_cover, theme["text"])
        y += 82
    _draw_text(cover_draw, subtitle_text, (124, y + 8), font_sub, theme["muted"])
    _draw_text(cover_draw, theme["cover_note"], (124, y + 62), font_small, theme["muted"])
    pill_x = 124
    for tag in cover_tags[:2]:
        pill = _draw_pill(cover_draw, tag, (pill_x, layout["cover_text_box"][3] - 84), font_tiny, theme["accent_soft"], theme["accent"], theme["border"])
        pill_x = pill[2] + 14

    point_photo_size = layout["point_photo_size"]
    if enlarge:
        point_photo_size = (point_photo_size[0] + 60, point_photo_size[1] + 60)
    points_photo = _fit_image(src, point_photo_size)
    points_img = Image.new("RGBA", (width, height), theme["background"])
    points_draw = ImageDraw.Draw(points_img)
    points_draw.rounded_rectangle((50, 50, 1030, 1390), radius=theme["radius"] + 8, fill=theme["card"])
    points_draw.rounded_rectangle(layout["point_photo_box"], radius=theme["radius"], fill=theme["photo_bg"], outline=theme["border"], width=2)
    points_img.alpha_composite(points_photo, _box_centered_position(layout["point_photo_box"], points_photo))
    _draw_text(points_draw, "这 3 点更容易种草", (126, 612), font_title, theme["text"])
    _draw_text(points_draw, "短标题 + 一句说明，读起来更像真实卖点", (128, 674), font_small, theme["muted"])
    for index, (box, number) in enumerate(layout["point_cards"]):
        points_draw.rounded_rectangle(box, radius=max(18, theme["radius"] - 4), fill=(255, 255, 255, 255), outline=theme["border"], width=2)
        _draw_pill(points_draw, number, (box[0] + 24, box[1] + 24), font_tiny, theme["accent_soft"], theme["accent"], theme["border"])
        _draw_text(points_draw, _clip_text(points[index], 14, "日常好物"), (box[0] + 130, box[1] + 34), font_title, theme["text"])
        _draw_text(points_draw, _point_detail_text(category, index, product_context), (box[0] + 130, box[1] + 86), font_small, theme["muted"])
        _draw_pill(points_draw, cover_tags[min(index, len(cover_tags) - 1)], (box[2] - 184, box[1] + 28), font_tiny, theme["accent_soft"], theme["accent"], theme["border"])

    summary_photo_size = layout["summary_photo_size"]
    if enlarge:
        summary_photo_size = (summary_photo_size[0] + 48, summary_photo_size[1] + 48)
    summary_photo = _fit_image(src, summary_photo_size)
    summary = Image.new("RGBA", (width, height), theme["background"])
    summary_draw = ImageDraw.Draw(summary)
    summary_draw.rounded_rectangle((50, 50, 1030, 1390), radius=theme["radius"] + 8, fill=theme["card"])
    _draw_pill(summary_draw, "最后一页更适合总结", (102, 96), font_small, theme["accent_soft"], theme["muted"], theme["border"])
    _draw_text(summary_draw, _clip_text(summary_title, 22, "适合日常轻分享"), (112, 188), font_title, theme["text"])
    summary_draw.rounded_rectangle(layout["summary_photo_box"], radius=theme["radius"], fill=theme["photo_bg"], outline=theme["border"], width=2)
    summary.alpha_composite(summary_photo, _box_centered_position(layout["summary_photo_box"], summary_photo))
    summary_boxes = [(110, 920, 970, 1048), (110, 1088, 970, 1216), (110, 1256, 970, 1384)]
    summary_texts = [
        _clip_text(suitable_for, 18, "喜欢轻分享的人"),
        _clip_text(recommend_reason, 22, "适合日常使用"),
        _clip_text(summary_sentence, 22, "一眼看懂推荐点"),
    ]
    for index, box in enumerate(summary_boxes):
        summary_draw.rounded_rectangle(box, radius=max(18, theme["radius"] - 6), fill=(255, 255, 255, 255), outline=theme["border"], width=2)
        _draw_pill(summary_draw, summary_labels[index], (box[0] + 24, box[1] + 20), font_tiny, theme["accent_soft"], theme["accent"], theme["border"])
        _draw_text(summary_draw, summary_texts[index], (box[0] + 28, box[1] + 72), font_small, theme["text"])
        _draw_text(summary_draw, "一眼看懂推荐点", (box[0] + 28, box[1] + 104), font_tiny, theme["muted"])

    variants = [cover, points_img, summary]
    paths = []
    source_stem = Path(input_image_path).stem or "sample"
    for idx, variant in enumerate(variants, start=1):
        suffix = ["cover", "points", "summary"][idx - 1]
        out_path = output_dir_path / f"poster_{idx}_{source_stem}_{suffix}.png"
        variant.save(out_path)
        paths.append(f"/static/generated/{out_path.name}")
    return paths


def compose_posters(
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
    return _render_variants(
        input_image_path,
        output_dir,
        title,
        subtitle,
        style,
        selling_points,
        summary_title,
        suitable_for,
        recommend_reason,
        summary_sentence,
        "其他好物",
        "",
        "",
        False,
    )


def compose_posters_enhanced(
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
    category: str = "其他好物",
    content_type: str = "",
    product_name: str = "",
) -> list[str]:
    return _render_variants(
        input_image_path,
        output_dir,
        title,
        subtitle,
        style,
        selling_points,
        summary_title,
        suitable_for,
        recommend_reason,
        summary_sentence,
        category,
        content_type,
        product_name,
        True,
    )
