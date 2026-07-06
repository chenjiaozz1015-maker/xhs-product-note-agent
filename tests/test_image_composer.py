from app.services.image_composer import (
    _category_tags,
    _get_style_layout,
    _point_detail_text,
    _resolve_product_context,
    _summary_label_text,
    compose_posters_enhanced,
    get_style_theme,
)


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


def test_all_five_styles_generate_three_posters(tmp_path):
    styles = ["清新简约", "可爱手账", "生活方式", "干货清单", "温柔日常"]

    for style in styles:
        image_paths = compose_posters_enhanced(
            input_image_path="missing-input.png",
            output_dir=str(tmp_path),
            title="水牛奶蛋糕 今日分享",
            subtitle="食品饮品｜好物推荐｜类目增强",
            style=style,
            selling_points=["下午茶更合适", "口感松软", "配咖啡牛奶都顺"],
            summary_title="水牛奶蛋糕的 3 个体验点",
            suitable_for="喜欢早餐和下午茶分享的人",
            recommend_reason="口感松软，适合家里囤一点",
            summary_sentence="适合早餐和下午茶场景",
            category="食品饮品",
            content_type="好物推荐",
            product_name="水牛奶蛋糕",
        )

        assert len(image_paths) == 3
        for image_path in image_paths:
            filename = image_path.rsplit("/", 1)[-1]
            assert (tmp_path / filename).exists()


def test_unknown_style_falls_back_and_still_generates_three_posters(tmp_path):
    image_paths = compose_posters_enhanced(
        input_image_path="missing-input.png",
        output_dir=str(tmp_path),
        title="随身护手霜",
        subtitle="美妆护肤｜真实测评｜未知风格",
        style="未知风格",
        selling_points=["随身带更方便", "滋润但不黏", "手部护理更顺手"],
        summary_title="随身护手霜使用感",
        suitable_for="喜欢通勤护理的人",
        recommend_reason="滋润舒服，日常护理顺手",
        summary_sentence="适合秋冬和随身护理场景",
        category="美妆护肤",
        content_type="真实测评",
        product_name="护手霜",
    )

    assert len(image_paths) == 3


def test_bakery_image_tags_and_copy_use_food_context():
    product_context = _resolve_product_context("食品饮品", "水牛奶蛋糕", "适合早餐和下午茶")

    assert product_context == "bakery"
    assert _category_tags("食品饮品", "好物推荐", product_context) == ["下午茶", "口感松软", "家里囤"]
    assert _point_detail_text("食品饮品", 0, product_context) == "下午茶拿出来刚刚好"
    assert _summary_label_text("食品饮品", product_context) == ["适合场景", "口感亮点", "分享理由"]


def test_drink_image_tags_use_drink_context():
    product_context = _resolve_product_context("食品饮品", "挂耳咖啡", "办公室早八备着喝")

    assert product_context == "drink"
    assert _category_tags("食品饮品", "好物推荐", product_context) == ["早八友好", "办公室", "冷冷热热都行"]


def test_cup_product_context_uses_cup_specific_tags_and_copy():
    product_context = _resolve_product_context("家居日用", "保温杯", "通勤带着方便")

    assert product_context == "cup_bottle"
    assert _category_tags("家居日用", "好物推荐", product_context) == ["通勤带", "容量刚好", "日常补水"]
    assert _point_detail_text("家居日用", 0, product_context) == "通勤带着方便"
    assert _point_detail_text("家居日用", 1, product_context) == "放包里也省心"
    assert _summary_label_text("家居日用", product_context)[2] == "日常补水"


def test_storage_and_cleaning_contexts_are_distinct():
    storage_context = _resolve_product_context("家居日用", "桌面收纳盒", "小空间分类更清楚")
    cleaning_context = _resolve_product_context("家居日用", "厨房清洁湿巾", "去污更直接")

    assert storage_context == "storage"
    assert cleaning_context == "cleaning"
    assert "桌面" in " ".join(_category_tags("家居日用", "好物推荐", storage_context))
    assert "清洁" in " ".join(_category_tags("家居日用", "好物推荐", cleaning_context))


def test_image_copy_has_no_system_prompt_labels():
    labels = _summary_label_text("食品饮品", "bakery")
    detail = _point_detail_text("家居日用", 0, "cup_bottle")
    forbidden = ["可直接拿来做发布说明", "可直接编辑后发布", "可复制发布", "发布说明", "生成后可修改"]

    joined = " ".join([*labels, detail, "一眼看懂推荐点"])
    assert all(word not in joined for word in forbidden)
