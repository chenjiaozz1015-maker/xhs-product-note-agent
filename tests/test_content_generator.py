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


def test_bakery_titles_body_and_tags_use_food_words():
    payload = generate_note_payload(
        product_name="水牛奶蛋糕",
        category="食品饮品",
        description="适合早餐和下午茶",
        content_type="好物推荐",
        style="清新简约",
    )
    joined = " ".join([
        *payload["note_titles"],
        payload["note_body"],
        *payload["hashtags"],
        *payload["selling_points"],
    ])

    assert payload["sub_category"] == "bakery"
    assert any(word in joined for word in ["早餐", "下午茶", "口感", "咖啡", "牛奶"])


def test_food_copy_avoids_beauty_and_household_words():
    payload = generate_note_payload(
        product_name="水牛奶蛋糕",
        category="其他好物",
        description="早餐和下午茶都可以吃，口感比较软，适合家里囤一点",
        content_type="好物推荐",
        style="温柔日常",
    )
    joined = " ".join([payload["note_body"], *payload["hashtags"], *payload["selling_points"]])

    assert payload["category"] == "食品饮品"
    forbidden_words = ["护肤", "上妆", "收纳", "清洁", "随手用", "功能产品", "小物"]
    assert all(word not in joined for word in forbidden_words)


def test_drink_profile_uses_drink_words():
    payload = generate_note_payload(
        product_name="挂耳咖啡",
        category="其他好物",
        description="办公室早八备着喝，搭早餐也自然",
        content_type="好物推荐",
        style="生活方式",
    )
    joined = " ".join([payload["note_body"], *payload["selling_points"], *payload["hashtags"]])

    assert payload["sub_category"] == "drink"
    assert any(word in joined for word in ["早八", "办公室", "早餐", "入口", "冷", "热"])


def test_hand_cream_copy_stays_in_hand_body_care_context():
    payload = generate_note_payload(
        product_name="护手霜",
        category="美妆护肤",
        description="放包里随身带，洗完手顺手涂一点",
        content_type="真实测评",
        style="清新简约",
    )
    joined = " ".join([payload["note_body"], *payload["hashtags"], *payload["selling_points"], payload["recommend_reason"]])

    assert payload["sub_category"] == "hand_body_care"
    assert any(word in joined for word in ["随身", "滋润", "手部", "秋冬", "不黏"])
    forbidden_words = ["早餐", "下午茶", "容量刚好", "厨房", "浴室", "收纳"]
    assert all(word not in joined for word in forbidden_words)


def test_makeup_copy_uses_makeup_words():
    payload = generate_note_payload(
        product_name="口红",
        category="美妆护肤",
        description="通勤妆提气色，上脸更自然",
        content_type="好物推荐",
        style="可爱手账",
    )
    joined = " ".join([payload["note_body"], *payload["hashtags"], *payload["selling_points"]])

    assert payload["sub_category"] == "makeup"
    assert any(word in joined for word in ["显色", "通勤妆", "提气色", "上脸", "妆感"])


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
        product_name="猫粮罐头",
        category="宠物用品",
        description="适合家里常备",
        content_type="好物推荐",
        style="清新简约",
    )
    joined = " ".join([*payload["note_titles"], payload["note_body"], *payload["hashtags"], *payload["selling_points"]])
    forbidden_words = ["上妆", "早餐", "面霜", "妆感", "护肤"]
    assert all(word not in joined for word in forbidden_words)


def test_cup_products_use_cup_copy_in_household_category():
    payload = generate_note_payload(
        product_name="保温杯",
        category="家居日用",
        description="通勤带着方便，放包里也省心",
        content_type="好物推荐",
        style="清新简约",
    )
    joined = " ".join([
        payload["note_body"],
        *payload["selling_points"],
        payload["recommend_reason"],
        payload["summary_sentence"],
        *payload["hashtags"],
    ])

    assert payload["sub_category"] == "cup_bottle"
    assert any(word in joined for word in ["通勤", "容量", "补水", "冷热饮", "杯"])
    forbidden_words = ["厨房", "浴室", "收纳", "小空间", "家务", "清洁"]
    assert all(word not in joined for word in forbidden_words)


def test_storage_products_use_storage_copy():
    payload = generate_note_payload(
        product_name="桌面收纳盒",
        category="家居日用",
        description="小空间分类更清楚，拿取更方便",
        content_type="好物推荐",
        style="干货清单",
    )
    joined = " ".join([payload["note_body"], *payload["selling_points"], *payload["hashtags"]])

    assert payload["sub_category"] == "storage"
    assert any(word in joined for word in ["桌面", "分类", "小空间", "拿取", "整理"])


def test_cleaning_products_use_cleaning_copy():
    payload = generate_note_payload(
        product_name="厨房清洁湿巾",
        category="家居日用",
        description="去污更直接，厨房浴室都能用",
        content_type="好物推荐",
        style="清新简约",
    )
    joined = " ".join([payload["note_body"], *payload["selling_points"], *payload["hashtags"]])

    assert payload["sub_category"] == "cleaning"
    assert any(word in joined for word in ["清洁", "厨房", "浴室", "去污", "家务"])
