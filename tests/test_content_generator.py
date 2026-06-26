from app.services.content_generator import generate_note_payload


def test_rule_based_content_generation_returns_expected_structure():
    payload = generate_note_payload(
        description="便携保温杯",
        content_type="好物推荐",
        style="清新简约",
    )

    assert payload["cover_title"]
    assert payload["cover_subtitle"]
    assert len(payload["selling_points"]) == 3
    assert len(payload["note_titles"]) == 5
    assert 6 <= len(payload["hashtags"]) <= 10
    assert len(payload["comments"]) == 3
    assert payload["note_body"]


def test_rule_based_content_generation_keeps_copy_short_and_safe():
    payload = generate_note_payload(
        description="",
        content_type="真实测评",
        style="清新简约",
    )

    assert len(payload["cover_title"]) <= 18
    assert len(payload["cover_subtitle"]) <= 20
    assert all(len(point) <= 20 for point in payload["selling_points"])
    assert len(payload["summary_sentence"]) <= 40
    assert all(word not in payload["cover_title"] for word in ["必买", "最强", "神器", "全网第一"])


def test_food_category_uses_food_related_copy():
    payload = generate_note_payload(
        product_name="水牛奶蛋糕",
        category="食品饮品",
        description="适合早餐和下午茶",
        content_type="好物推荐",
        style="清新简约",
    )

    joined = " ".join(
        [
            *payload["note_titles"],
            payload["note_body"],
            *payload["hashtags"],
            *payload["selling_points"],
        ]
    )

    assert any(word in joined for word in ["早餐", "下午茶", "口感", "食品", "囤货"])


def test_food_category_avoids_beauty_words():
    payload = generate_note_payload(
        product_name="水牛奶蛋糕",
        category="食品饮品",
        description="适合早餐和下午茶",
        content_type="好物推荐",
        style="清新简约",
    )
    joined = " ".join([*payload["note_titles"], payload["note_body"], *payload["hashtags"], *payload["selling_points"]])

    forbidden_words = ["护肤", "上妆", "肤感", "保湿", "精华", "面霜", "妆感", "美白", "修护"]
    assert all(word not in joined for word in forbidden_words)


def test_product_name_enters_title_or_body():
    payload = generate_note_payload(
        product_name="水牛奶蛋糕",
        category="食品饮品",
        description="适合早餐",
        content_type="好物推荐",
        style="清新简约",
    )

    assert any("水牛奶蛋糕" in title for title in payload["note_titles"])
    assert "水牛奶蛋糕" in payload["note_body"]


def test_beauty_category_avoids_food_words():
    payload = generate_note_payload(
        product_name="护手霜",
        category="美妆护肤",
        description="通勤随身带",
        content_type="真实测评",
        style="清新简约",
    )
    joined = " ".join([*payload["note_titles"], payload["note_body"], *payload["hashtags"], *payload["selling_points"]])

    forbidden_words = ["早餐", "下午茶", "零食", "口感", "囤粮", "猫咪", "狗狗"]
    assert all(word not in joined for word in forbidden_words)


def test_generated_lists_do_not_repeat():
    payload = generate_note_payload(
        product_name="水牛奶蛋糕",
        category="食品饮品",
        description="适合早餐",
        content_type="好物推荐",
        style="清新简约",
    )

    assert len(payload["note_titles"]) == len(set(payload["note_titles"]))
    assert len(payload["hashtags"]) == len(set(payload["hashtags"]))
    assert len(payload["selling_points"]) == len(set(payload["selling_points"]))


def test_pet_category_avoids_beauty_and_food_words():
    payload = generate_note_payload(
        product_name="猫粮勺",
        category="宠物用品",
        description="适合家里常备",
        content_type="好物推荐",
        style="清新简约",
    )
    joined = " ".join([*payload["note_titles"], payload["note_body"], *payload["hashtags"], *payload["selling_points"]])

    forbidden_words = ["上妆", "早餐", "面霜", "妆感", "护肤"]
    assert all(word not in joined for word in forbidden_words)


def test_food_keywords_resolve_to_food_copy_even_when_category_is_generic():
    payload = generate_note_payload(
        product_name="水牛奶蛋糕",
        category="其他好物",
        description="早餐和下午茶都可以吃，口感比较软，适合家里囤一点",
        content_type="好物推荐",
        style="温柔日常",
    )
    joined = " ".join([payload["note_body"], *payload["selling_points"], payload["recommend_reason"], payload["summary_sentence"]])

    assert payload["category"] == "食品饮品"
    assert any(word in joined for word in ["早餐", "下午茶", "口感", "囤"])
    forbidden_words = ["随手用", "随手放", "小物", "功能", "提升日常体验", "使用频率"]
    assert all(word not in joined for word in forbidden_words)
