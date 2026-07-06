from app.services.category_profile import detect_product_profile


def test_bakery_profile_detected_from_cake_keywords():
    profile = detect_product_profile("水牛奶蛋糕", "其他好物", "适合早餐和下午茶")

    assert profile.main_category == "food"
    assert profile.sub_category == "bakery"


def test_drink_profile_detected_from_coffee_keywords():
    profile = detect_product_profile("挂耳咖啡", "其他好物", "办公室早八备着喝")

    assert profile.main_category == "food"
    assert profile.sub_category == "drink"


def test_snack_profile_detected_from_snack_keywords():
    profile = detect_product_profile("坚果零食", "其他好物", "适合办公室备一点")

    assert profile.main_category == "food"
    assert profile.sub_category == "snack"


def test_light_meal_profile_detected_from_oat_keywords():
    profile = detect_product_profile("燕麦代餐杯", "其他好物", "工作日早餐更省心")

    assert profile.main_category == "food"
    assert profile.sub_category == "light_meal"


def test_hand_body_care_profile_detected_for_hand_cream():
    profile = detect_product_profile("护手霜", "美妆护肤", "秋冬放包里随身带")

    assert profile.main_category == "beauty"
    assert profile.sub_category == "hand_body_care"


def test_makeup_profile_detected_for_lipstick():
    profile = detect_product_profile("口红", "美妆护肤", "通勤妆提气色")

    assert profile.main_category == "beauty"
    assert profile.sub_category == "makeup"


def test_skincare_profile_detected_for_serum():
    profile = detect_product_profile("修护精华", "美妆护肤", "换季补水保湿")

    assert profile.main_category == "beauty"
    assert profile.sub_category == "skincare"


def test_cup_bottle_profile_detected_for_thermos():
    profile = detect_product_profile("保温杯", "家居日用", "通勤带着方便")

    assert profile.main_category == "home"
    assert profile.sub_category == "cup_bottle"


def test_storage_profile_detected_for_storage_box():
    profile = detect_product_profile("桌面收纳盒", "家居日用", "小空间分类更清楚")

    assert profile.main_category == "home"
    assert profile.sub_category == "storage"


def test_cleaning_profile_detected_for_wet_wipes():
    profile = detect_product_profile("厨房清洁湿巾", "家居日用", "去污更直接")

    assert profile.main_category == "home"
    assert profile.sub_category == "cleaning"
