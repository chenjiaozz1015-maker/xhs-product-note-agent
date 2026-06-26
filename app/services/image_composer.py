from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from app.config import FONTS_DIR, GENERATED_DIR, STATIC_DIR


PROJECT_CJK_FONT_PATHS = (
    FONTS_DIR / "NotoSansSC-Regular.ttf",
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


STYLE_THEMES = {
    "清新简约": {
        "background": (248, 250, 248, 255),
        "card": (255, 255, 255, 246),
        "photo_bg": (239, 247, 241, 255),
        "accent": (91, 158, 132, 255),
        "accent_soft": (222, 242, 232, 255),
        "text": (39, 48, 44, 255),
        "muted": (98, 120, 110, 255),
        "border": (218, 232, 224, 255),
        "radius": 30,
        "decoration": "minimal",
        "point_label": "dot",
        "summary_marker": "label",
        "cover_badge": "好物推荐",
        "cover_note": "简洁排版 · 一键发布",
    },
    "可爱手账": {
        "background": (255, 246, 239, 255),
        "card": (255, 255, 255, 246),
        "photo_bg": (255, 235, 225, 255),
        "accent": (255, 125, 148, 255),
        "accent_soft": (255, 230, 236, 255),
        "text": (64, 48, 47, 255),
        "muted": (151, 96, 92, 255),
        "border": (248, 209, 199, 255),
        "radius": 46,
        "decoration": "stickers",
        "point_label": "sticker",
        "summary_marker": "sticker",
        "cover_badge": "今日分享",
        "cover_note": "手账感小卡片",
    },
    "生活方式": {
        "background": (246, 242, 235, 255),
        "card": (255, 254, 250, 246),
        "photo_bg": (236, 229, 219, 255),
        "accent": (142, 113, 82, 255),
        "accent_soft": (235, 222, 204, 255),
        "text": (45, 41, 36, 255),
        "muted": (116, 105, 92, 255),
        "border": (224, 214, 200, 255),
        "radius": 26,
        "decoration": "magazine",
        "point_label": "line",
        "summary_marker": "label",
        "cover_badge": "生活好物",
        "cover_note": "最近常用的日常分享",
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
        "radius": 22,
        "decoration": "checklist",
        "point_label": "number",
        "summary_marker": "check",
        "cover_badge": "种草清单",
        "cover_note": "这几点值得看",
    },
    "温柔日常": {
        "background": (255, 248, 241, 255),
        "card": (255, 253, 249, 246),
        "photo_bg": (255, 239, 229, 255),
        "accent": (224, 143, 132, 255),
        "accent_soft": (255, 232, 226, 255),
        "text": (64, 50, 45, 255),
        "muted": (132, 97, 88, 255),
        "border": (244, 215, 204, 255),
        "radius": 40,
        "decoration": "soft_dots",
        "point_label": "soft",
        "summary_marker": "soft",
        "cover_badge": "温柔日常",
        "cover_note": "慢慢用下来还挺喜欢",
    },
}


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


def _draw_theme_decoration(draw: ImageDraw.ImageDraw, theme: dict, width: int, height: int) -> None:
    accent = theme["accent"]
    soft = theme["accent_soft"]
    muted = theme["muted"]
    decoration = theme["decoration"]

    if decoration == "stickers":
        draw.rounded_rectangle((770, 98, 970, 152), radius=18, fill=soft, outline=theme["border"], width=2)
        draw.rectangle((792, 82, 898, 112), fill=(255, 218, 126, 210))
        for x, y in [(90, 112), (956, 250), (142, 1270), (922, 1192)]:
            draw.ellipse((x, y, x + 24, y + 24), fill=accent)
    elif decoration == "magazine":
        draw.line((88, 112, 330, 112), fill=accent, width=5)
        draw.line((750, height - 138, 988, height - 138), fill=theme["border"], width=4)
        draw.rectangle((916, 86, 958, 188), fill=soft)
    elif decoration == "checklist":
        for y in (116, 156, 196):
            draw.line((848, y, 982, y), fill=theme["border"], width=4)
            draw.rounded_rectangle((800, y - 14, 826, y + 12), radius=6, outline=accent, width=3)
        draw.line((118, height - 112, 962, height - 112), fill=theme["border"], width=3)
    elif decoration == "soft_dots":
        for x, y, r in [(82, 120, 18), (944, 132, 26), (892, 1258, 18), (134, 1210, 12)]:
            draw.ellipse((x, y, x + r, y + r), fill=soft)
    else:
        draw.rounded_rectangle((886, 98, 960, 134), radius=18, fill=soft)
        draw.ellipse((104, 118, 132, 146), fill=soft)


def _draw_point_label(draw: ImageDraw.ImageDraw, theme: dict, box: tuple[int, int, int, int], number: str, font: ImageFont.ImageFont) -> int:
    accent = theme["accent"]
    soft = theme["accent_soft"]
    text = theme["text"]
    label_style = theme["point_label"]

    if label_style == "number":
        _draw_text(draw, number, (box[0] + 34, box[1] + 44), font, accent)
        draw.line((box[0] + 34, box[1] + 88, box[0] + 92, box[1] + 88), fill=accent, width=4)
        return box[0] + 130
    if label_style == "sticker":
        draw.rounded_rectangle((box[0] + 24, box[1] + 34, box[0] + 184, box[1] + 96), radius=20, fill=soft, outline=theme["border"], width=2)
        _draw_text(draw, f"喜欢点 {int(number)}", (box[0] + 40, box[1] + 48), font, accent)
        return box[0] + 214
    if label_style == "line":
        draw.line((box[0] + 34, box[1] + 42, box[0] + 34, box[1] + 104), fill=accent, width=6)
        _draw_text(draw, number, (box[0] + 58, box[1] + 50), font, text)
        return box[0] + 126
    if label_style == "soft":
        draw.ellipse((box[0] + 30, box[1] + 38, box[0] + 94, box[1] + 102), fill=soft)
        _draw_text(draw, number, (box[0] + 46, box[1] + 50), font, accent)
        return box[0] + 124

    draw.ellipse((box[0] + 30, box[1] + 38, box[0] + 94, box[1] + 102), fill=accent)
    _draw_text(draw, number, (box[0] + 45, box[1] + 50), font, (255, 255, 255, 255))
    return box[0] + 124


def _summary_label(theme: dict, label: str) -> str:
    if theme["summary_marker"] == "check":
        return f"✓ {label}"
    if theme["summary_marker"] == "sticker":
        return f"✦ {label}"
    if theme["summary_marker"] == "soft":
        return f"· {label}"
    return label


def _get_style_layout(decoration: str) -> dict:
    layouts = {
        "minimal": {
            "cover_photo_box": (92, 108, 988, 850),
            "cover_photo_size": (830, 700),
            "cover_text_box": (80, 900, 1000, 1338),
            "cover_badge_pos": (146, 140),
            "cover_text_badge_pos": (146, 980),
            "cover_title_pos": (116, 1070),
            "cover_subtitle_pos": (118, 1180),
            "cover_note_pos": (118, 1250),
            "points_photo_box": (88, 92, 992, 620),
            "points_photo_size": (820, 470),
            "points_heading_box": (92, 665, 988, 755),
            "points_heading_pos": (126, 683),
            "point_cards": [
                ((116, 820, 964, 960), "01"),
                ((116, 1000, 964, 1140), "02"),
                ((116, 1180, 964, 1320), "03"),
            ],
            "summary_photo_box": (250, 330, 830, 850),
            "summary_photo_size": (560, 500),
            "summary_cards": [
                ((92, 930, 988, 1050), "适合谁"),
                ((92, 1085, 988, 1205), "推荐理由"),
                ((92, 1240, 988, 1360), "一句话总结"),
            ],
        },
        "stickers": {
            "cover_photo_box": (122, 180, 958, 850),
            "cover_photo_size": (740, 600),
            "cover_text_box": (86, 905, 994, 1342),
            "cover_badge_pos": (144, 130),
            "cover_text_badge_pos": (146, 970),
            "cover_title_pos": (116, 1062),
            "cover_subtitle_pos": (118, 1176),
            "cover_note_pos": (118, 1254),
            "points_photo_box": (104, 96, 976, 540),
            "points_photo_size": (720, 390),
            "points_heading_box": (112, 590, 968, 678),
            "points_heading_pos": (150, 608),
            "point_cards": [
                ((92, 735, 900, 880), "01"),
                ((178, 925, 988, 1070), "02"),
                ((92, 1115, 900, 1260), "03"),
            ],
            "summary_photo_box": (280, 330, 800, 810),
            "summary_photo_size": (500, 450),
            "summary_cards": [
                ((112, 900, 968, 1028), "适合谁"),
                ((112, 1070, 968, 1198), "推荐理由"),
                ((112, 1240, 968, 1368), "一句话总结"),
            ],
        },
        "magazine": {
            "cover_photo_box": (72, 96, 1008, 920),
            "cover_photo_size": (900, 790),
            "cover_text_box": (96, 930, 984, 1328),
            "cover_badge_pos": (128, 122),
            "cover_text_badge_pos": (132, 990),
            "cover_title_pos": (128, 1080),
            "cover_subtitle_pos": (130, 1184),
            "cover_note_pos": (130, 1256),
            "points_photo_box": (88, 92, 992, 720),
            "points_photo_size": (880, 580),
            "points_heading_box": (100, 760, 980, 840),
            "points_heading_pos": (132, 776),
            "point_cards": [
                ((110, 900, 470, 1298), "01"),
                ((510, 900, 970, 1018), "02"),
                ((510, 1060, 970, 1298), "03"),
            ],
            "summary_photo_box": (90, 330, 990, 880),
            "summary_photo_size": (860, 520),
            "summary_cards": [
                ((92, 945, 988, 1065), "适合谁"),
                ((92, 1102, 988, 1222), "推荐理由"),
                ((92, 1259, 988, 1379), "一句话总结"),
            ],
        },
        "checklist": {
            "cover_photo_box": (118, 300, 962, 860),
            "cover_photo_size": (800, 520),
            "cover_text_box": (86, 86, 994, 278),
            "cover_badge_pos": (134, 116),
            "cover_text_badge_pos": (118, 930),
            "cover_title_pos": (118, 1010),
            "cover_subtitle_pos": (120, 1122),
            "cover_note_pos": (120, 1200),
            "points_photo_box": (104, 92, 976, 470),
            "points_photo_size": (760, 340),
            "points_heading_box": (100, 510, 980, 600),
            "points_heading_pos": (132, 528),
            "point_cards": [
                ((100, 655, 980, 825), "01"),
                ((100, 880, 980, 1050), "02"),
                ((100, 1105, 980, 1275), "03"),
            ],
            "summary_photo_box": (112, 300, 968, 705),
            "summary_photo_size": (780, 360),
            "summary_cards": [
                ((100, 780, 980, 930), "适合谁"),
                ((100, 970, 980, 1120), "推荐理由"),
                ((100, 1160, 980, 1310), "一句话总结"),
            ],
        },
        "soft_dots": {
            "cover_photo_box": (114, 240, 966, 870),
            "cover_photo_size": (800, 580),
            "cover_text_box": (92, 110, 988, 232),
            "cover_badge_pos": (140, 132),
            "cover_text_badge_pos": (122, 950),
            "cover_title_pos": (116, 1028),
            "cover_subtitle_pos": (118, 1140),
            "cover_note_pos": (118, 1220),
            "points_photo_box": (120, 110, 960, 560),
            "points_photo_size": (760, 400),
            "points_heading_box": (116, 615, 964, 700),
            "points_heading_pos": (154, 632),
            "point_cards": [
                ((126, 760, 954, 902), "01"),
                ((126, 945, 954, 1087), "02"),
                ((126, 1130, 954, 1272), "03"),
            ],
            "summary_photo_box": (238, 320, 842, 830),
            "summary_photo_size": (580, 480),
            "summary_cards": [
                ((108, 920, 972, 1044), "适合谁"),
                ((108, 1085, 972, 1209), "推荐理由"),
                ((108, 1250, 972, 1374), "一句话总结"),
            ],
        },
    }
    return layouts.get(decoration, layouts["minimal"])


def _box_centered_position(box: tuple[int, int, int, int], image: Image.Image, y_offset: int = 0) -> tuple[int, int]:
    return (
        box[0] + (box[2] - box[0] - image.width) // 2,
        box[1] + (box[3] - box[1] - image.height) // 2 + y_offset,
    )


def _prepare_cover_photo(src: Image.Image, theme: dict, size: tuple[int, int]) -> Image.Image:
    photo = _fit_image(src, size)
    if theme["decoration"] == "stickers":
        return photo.rotate(-2, resample=Image.Resampling.BICUBIC, expand=True)
    return photo


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
    output_dir_path = Path(output_dir or GENERATED_DIR)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    src = _load_source_image(input_image_path)
    width, height = 1080, 1440
    theme = get_style_theme(style)
    radius = theme["radius"]
    layout = _get_style_layout(theme["decoration"])

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

    cover_photo = _prepare_cover_photo(src, theme, layout["cover_photo_size"])
    cover = Image.new("RGBA", (width, height), theme["background"])
    cover_draw = ImageDraw.Draw(cover)
    cover_draw.rounded_rectangle((56, 60, 1024, 1370), radius=radius + 10, fill=theme["card"])
    _draw_theme_decoration(cover_draw, theme, width, height)
    cover_photo_box = layout["cover_photo_box"]
    cover_text_box = layout["cover_text_box"]
    cover_draw.rounded_rectangle(cover_photo_box, radius=radius, fill=theme["photo_bg"], outline=theme["border"], width=2)
    cover.alpha_composite(cover_photo, _box_centered_position(cover_photo_box, cover_photo))
    cover_draw.rounded_rectangle(cover_text_box, radius=radius, fill=(255, 255, 255, 252), outline=theme["border"], width=2)
    badge_x, badge_y = layout["cover_badge_pos"]
    cover_draw.rounded_rectangle((badge_x - 30, badge_y - 14, badge_x + 220, badge_y + 48), radius=26, fill=theme["accent"])
    text_badge_x, text_badge_y = layout["cover_text_badge_pos"]
    cover_draw.rounded_rectangle((text_badge_x - 30, text_badge_y - 16, text_badge_x + 220, text_badge_y + 54), radius=26, fill=theme["accent"])
    _draw_text(cover_draw, theme["cover_badge"], (badge_x, badge_y), font_small, (255, 255, 255, 255))
    _draw_text(cover_draw, theme["cover_badge"], (text_badge_x, text_badge_y), font_small, (255, 255, 255, 255))
    _draw_text(cover_draw, short_title, layout["cover_title_pos"], font_cover_title, theme["text"])
    _draw_text(cover_draw, short_subtitle, layout["cover_subtitle_pos"], font_sub, theme["muted"])
    _draw_text(cover_draw, theme["cover_note"], layout["cover_note_pos"], font_small, theme["muted"])

    points_photo = _fit_image(src, layout["points_photo_size"])
    points = Image.new("RGBA", (width, height), theme["background"])
    points_draw = ImageDraw.Draw(points)
    points_draw.rounded_rectangle((48, 48, 1032, 1392), radius=radius + 10, fill=theme["card"])
    _draw_theme_decoration(points_draw, theme, width, height)
    points_photo_box = layout["points_photo_box"]
    points_draw.rounded_rectangle(points_photo_box, radius=radius, fill=theme["photo_bg"], outline=theme["border"], width=2)
    points.alpha_composite(points_photo, _box_centered_position(points_photo_box, points_photo))
    points_heading = "3 个真实体验点" if theme["decoration"] == "checklist" else "我喜欢它的 3 个点"
    points_draw.rounded_rectangle(layout["points_heading_box"], radius=radius, fill=theme["accent_soft"], outline=theme["border"], width=2)
    _draw_text(points_draw, points_heading, layout["points_heading_pos"], font_title, theme["text"])

    for index, (box, number) in enumerate(layout["point_cards"]):
        text = point_texts[index][:18]
        points_draw.rounded_rectangle(box, radius=max(18, radius - 4), fill=(255, 255, 255, 255), outline=theme["border"], width=2)
        text_x = _draw_point_label(points_draw, theme, box, number, font_small)
        _draw_text(points_draw, text, (text_x, box[1] + 48), font_card, theme["text"])

    summary_photo = _fit_image(src, layout["summary_photo_size"])
    summary = Image.new("RGBA", (width, height), theme["background"])
    summary_draw = ImageDraw.Draw(summary)
    summary_draw.rounded_rectangle((48, 48, 1032, 1392), radius=radius + 10, fill=theme["card"])
    _draw_theme_decoration(summary_draw, theme, width, height)
    summary_draw.rounded_rectangle((88, 88, 992, 210), radius=radius, fill=theme["accent_soft"], outline=theme["border"], width=2)
    summary_heading = "最后想说" if theme["decoration"] != "checklist" else "清单总结"
    _draw_text(summary_draw, summary_heading, (128, 112), font_sub, theme["muted"])
    _draw_text(summary_draw, summary_title_text, (128, 250), font_title, theme["text"])
    photo_box = layout["summary_photo_box"]
    summary_draw.rounded_rectangle(photo_box, radius=radius, fill=theme["photo_bg"], outline=theme["border"], width=2)
    summary.alpha_composite(summary_photo, _box_centered_position(photo_box, summary_photo))

    summary_texts = [suitable_for_text, recommend_reason_text, summary_sentence_text]
    for index, (box, label) in enumerate(layout["summary_cards"]):
        text = summary_texts[index]
        summary_draw.rounded_rectangle(box, radius=max(18, radius - 8), fill=(255, 255, 255, 255), outline=theme["border"], width=2)
        _draw_text(summary_draw, _summary_label(theme, label), (box[0] + 34, box[1] + 24), font_card_small, theme["accent"])
        _draw_text(summary_draw, text, (box[0] + 260, box[1] + 24), font_card, theme["text"])

    variants = [cover, points, summary]
    paths = []
    source_stem = Path(input_image_path).stem or "sample"
    for idx, variant in enumerate(variants, start=1):
        suffix = ["cover", "points", "summary"][idx - 1]
        out_path = output_dir_path / f"poster_{idx}_{source_stem}_{suffix}.png"
        variant.save(out_path)
        paths.append(f"/static/generated/{out_path.name}")
    return paths
