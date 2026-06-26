from app.services.image_composer import _get_style_layout, get_style_theme


def test_clean_style_theme_is_valid():
    theme = get_style_theme("清新简约")

    assert theme["background"]
    assert theme["card"]
    assert theme["accent"]
    assert theme["decoration"] == "minimal"


def test_cute_style_theme_differs_from_clean_style():
    clean = get_style_theme("清新简约")
    cute = get_style_theme("可爱手账")

    assert cute["background"] != clean["background"]
    assert cute["radius"] != clean["radius"]
    assert cute["decoration"] == "stickers"


def test_checklist_style_theme_uses_list_decoration():
    theme = get_style_theme("干货清单")

    assert theme["decoration"] == "checklist"
    assert theme["point_label"] == "number"
    assert theme["summary_marker"] == "check"


def test_unknown_style_falls_back_to_clean_style():
    assert get_style_theme("未知风格") == get_style_theme("清新简约")


def test_styles_use_different_layout_structures():
    clean = _get_style_layout(get_style_theme("清新简约")["decoration"])
    cute = _get_style_layout(get_style_theme("可爱手账")["decoration"])
    lifestyle = _get_style_layout(get_style_theme("生活方式")["decoration"])
    checklist = _get_style_layout(get_style_theme("干货清单")["decoration"])

    assert clean["cover_photo_box"] != cute["cover_photo_box"]
    assert lifestyle["cover_photo_box"][3] > clean["cover_photo_box"][3]
    assert checklist["point_cards"][0][1] == "01"
    assert checklist["point_cards"][0][0] != clean["point_cards"][0][0]
