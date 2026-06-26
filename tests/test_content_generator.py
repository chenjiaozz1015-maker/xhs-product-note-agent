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
    assert len(payload["hashtags"]) == 10
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

    assert any("水牛奶蛋糕" in title for title in payload["note_titles"]) or "水牛奶蛋糕" in payload["note_body"]
