from __future__ import annotations

from typing import Dict


CATEGORY_TEMPLATES = {
    "食品饮品": {
        "focus": ["口感舒服", "日常方便", "早餐下午茶都合适"],
        "titles": ["适合日常囤的", "早餐下午茶都能吃的", "办公室也适合的", "最近回购的", "家里可以备一点的"],
        "hashtags": ["#食品分享", "#早餐推荐", "#下午茶", "#好物分享", "#日常囤货", "#办公室小零食", "#回购分享"],
        "suitable_for": "喜欢早餐和下午茶分享的人",
        "recommend_reason": "口感顺、拿取方便、适合日常囤一点",
        "comments": ["你平时会囤这类吃的吗？", "早餐还是下午茶，你更想怎么搭？", "还想看哪些日常食品分享？"],
        "body": "这次分享的是{name}，日常吃起来比较方便，口感也很适合早餐或下午茶。家里、办公室都能备一点，想吃的时候不用太费心。整体是那种不会很复杂，但很容易融入日常的小东西。",
    },
    "美妆护肤": {
        "focus": ["质地舒服", "肤感清爽", "日常护理很顺手"],
        "titles": ["最近常用的", "通勤也适合的", "肤感挺舒服的", "日常护理会用到的", "想空瓶回购的"],
        "hashtags": ["#护肤分享", "#美妆好物", "#空瓶回购", "#日常护肤", "#通勤好物", "#护肤日常", "#真实测评"],
        "suitable_for": "喜欢日常护肤和通勤好物的人",
        "recommend_reason": "质地舒服、肤感清爽、日常护理顺手",
        "comments": ["你更在意质地还是肤感？", "这类护肤好物你会想试试吗？", "还想看哪些日常护理分享？"],
        "body": "这次分享的是{name}，用下来最明显的感受是质地和肤感都比较舒服。日常护理或通勤前后使用都不麻烦，整体不会给人很重的负担感。适合想把护肤步骤做得简单一点的人参考。",
    },
    "家居日用": {
        "focus": ["日常实用", "收纳清洁更顺手", "质感在线"],
        "titles": ["让日常更顺手的", "家里用着很方便的", "提升生活感的", "实用感不错的", "最近很常用的"],
        "hashtags": ["#家居好物", "#生活好物", "#收纳整理", "#日用分享", "#实用好物", "#居家日常", "#好物分享"],
        "suitable_for": "喜欢实用家居和日用分享的人",
        "recommend_reason": "实用、方便、能让日常更顺手",
        "comments": ["你家里最需要哪类日用好物？", "这类实用分享你想继续看吗？", "你更喜欢收纳还是清洁类好物？"],
        "body": "这次分享的是{name}，属于日常里很容易用上的家居日用好物。它不需要复杂操作，放在家里能让使用、收纳或清洁都更顺手。整体质感也比较舒服，适合想轻松提升生活感的人。",
    },
    "母婴儿童": {
        "focus": ["日常使用方便", "外出携带顺手", "亲子场景适合"],
        "titles": ["带娃日常会用到的", "亲子生活里挺方便的", "外出也顺手的", "孩子日常适合的", "宝妈可以参考的"],
        "hashtags": ["#母婴好物", "#育儿日常", "#亲子生活", "#带娃日常", "#宝妈分享", "#母婴分享", "#好物分享"],
        "suitable_for": "关注亲子生活和带娃日常的人",
        "recommend_reason": "日常使用方便，外出或收纳都比较顺手",
        "comments": ["带娃日常你最需要哪类好物？", "你会关注方便携带这一点吗？", "还想看哪些亲子生活分享？"],
        "body": "这次分享的是{name}，更适合放在日常亲子场景里看。它使用起来比较方便，外出或家里收纳都能轻松一点。不是夸张型推荐，只是作为带娃日常里的一个实用参考。",
    },
    "宠物用品": {
        "focus": ["日常照顾方便", "适口性友好", "适合囤货"],
        "titles": ["养宠日常会用到的", "猫狗日常挺方便的", "适合家里备一点的", "最近觉得顺手的", "养宠人可以参考的"],
        "hashtags": ["#宠物用品", "#养宠好物", "#猫咪日常", "#狗狗日常", "#宠物日常", "#养宠分享", "#好物分享"],
        "suitable_for": "关注宠物日常照顾的人",
        "recommend_reason": "方便照顾，日常使用和囤货都比较省心",
        "comments": ["你家宠物更挑哪一点？", "养宠日常你最想省心的是什么？", "还想看哪些宠物用品分享？"],
        "body": "这次分享的是{name}，放在养宠日常里还挺实用。使用起来比较方便，也适合日常照顾或家里备一点。整体更偏省心型，不需要复杂操作，养宠人可以参考看看。",
    },
    "服饰配件": {
        "focus": ["日常好搭", "通勤舒服", "质感显气质"],
        "titles": ["日常搭配很顺手的", "通勤也能用的", "质感挺加分的", "最近常搭的", "显气质的小配件"],
        "hashtags": ["#穿搭分享", "#配饰分享", "#通勤穿搭", "#日常穿搭", "#质感穿搭", "#好物分享", "#搭配灵感"],
        "suitable_for": "喜欢日常穿搭和通勤搭配的人",
        "recommend_reason": "好搭、舒服、能给日常造型加一点质感",
        "comments": ["你更喜欢通勤风还是休闲风？", "这类搭配你会想试试吗？", "还想看哪些配饰分享？"],
        "body": "这次分享的是{name}，日常搭配起来比较顺手。它的质感和舒适度都还不错，通勤或休闲场景都能自然融进去。适合想让穿搭更轻松、更有细节感的人参考。",
    },
    "其他好物": {
        "focus": ["日常好用", "方便顺手", "质感舒服"],
        "titles": ["真的很适合日常的", "最近很喜欢的", "让我觉得省心的", "很值得试试的", "想认真分享的"],
        "hashtags": ["#好物分享", "#日常好物", "#小红书种草", "#真实体验", "#好物推荐", "#生活好物", "#好用分享"],
        "suitable_for": "喜欢日常好物分享的人",
        "recommend_reason": "好用、方便、让日常更轻松",
        "comments": ["你平时最在意哪一点？", "如果你也想看更多实用分享，我可以继续整理", "这类好物你会不会想试试？"],
        "body": "这次分享的是{name}，整体体验还挺顺手的。它的样子和使用感都比较舒服，日常带着或者在家里用都很方便。如果你也想找一个不复杂、但又有点好用感觉的好物，可以参考看看。",
    },
}


def _safe_text(value: str, fallback: str) -> str:
    cleaned = "".join(ch for ch in value.strip() if ch not in ["\n", "\r", "\t"])
    return cleaned or fallback


def generate_note_payload(
    description: str,
    content_type: str,
    style: str,
    product_name: str = "",
    category: str = "其他好物",
) -> Dict[str, object]:
    category_value = category if category in CATEGORY_TEMPLATES else "其他好物"
    template = CATEGORY_TEMPLATES[category_value]
    product_value = _safe_text(product_name, "这个好物")
    description_value = _safe_text(description, "这件小东西")
    content_type_value = _safe_text(content_type, "好物推荐")
    style_value = _safe_text(style, "清新简约")

    display_name = product_value[:10]
    detail_hint = "" if description_value == "这件小东西" else f" {description_value}"

    selling_points = [f"{display_name}{point}"[:20] for point in template["focus"]]

    title_directions = template["titles"]
    note_titles = [
        f"{display_name}，{title_directions[0]}",
        f"最近喜欢的{display_name}",
        f"{title_directions[1]}{display_name}",
        f"{display_name}真实分享：{title_directions[2]}",
        f"不夸张，{display_name}我会继续用",
    ]

    cover_title = f"{display_name}，真实分享"
    if len(cover_title) > 18:
        cover_title = cover_title[:18]

    cover_subtitle = f"{category_value}｜{content_type_value}｜{style_value}"
    if len(cover_subtitle) > 20:
        cover_subtitle = cover_subtitle[:20]

    summary_sentence = f"如果你也在看{display_name}，这款可以作为日常参考。"
    if len(summary_sentence) > 40:
        summary_sentence = summary_sentence[:40]

    hashtags = (template["hashtags"] + ["#小红书种草", "#真实体验", "#种草笔记"])[:10]

    return {
        "cover_title": cover_title,
        "cover_subtitle": cover_subtitle,
        "selling_points": selling_points,
        "summary_title": f"关于{display_name}，我想说这几点"[:24],
        "suitable_for": template["suitable_for"],
        "recommend_reason": template["recommend_reason"],
        "summary_sentence": summary_sentence,
        "note_titles": note_titles,
        "note_body": template["body"].format(name=product_value) + detail_hint,
        "hashtags": hashtags,
        "comments": template["comments"],
        "product_name": product_value,
        "category": category_value,
    }
