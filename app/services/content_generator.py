from __future__ import annotations

from typing import Dict, Iterable


CATEGORY_TEMPLATES = {
    "食品饮品": {
        "fallback": "这个好物",
        "title_patterns": [
            "{name}，最近早餐经常吃它",
            "这款{name}，放办公室也挺方便",
            "下午茶不知道吃什么，可以看看{name}",
            "不夸张，{name}我会继续囤",
            "家里人也能接受的日常小点心",
        ],
        "selling_points": [
            "早餐下午茶都能搭",
            "软乎口感更日常",
            "适合家里囤一点",
            "办公室家里都能吃",
            "分享给家人也自然",
        ],
        "focus": ["口感舒服", "日常方便", "早餐下午茶都合适"],
        "titles": ["适合日常囤的", "早餐下午茶都能吃的", "办公室也适合的", "最近回购的", "家里可以备一点的"],
        "hashtags": ["#食品分享", "#早餐推荐", "#下午茶", "#好物分享", "#日常囤货", "#办公室小零食", "#回购分享"],
        "suitable_for": "喜欢早餐和下午茶分享的人",
        "recommend_reason": "口感软、早餐下午茶都能搭、适合日常囤一点",
        "comments": ["你平时会囤这类吃的吗？", "早餐还是下午茶，你更想怎么搭？", "还想看哪些日常食品分享？"],
        "body": [
            "最近早餐和下午茶会吃到{name}，想吃点软乎的小点心时拿一份很方便。",
            "它更适合放在家里或办公室当日常补充，口感比较软，搭牛奶、咖啡或者茶都不突兀。家里人一起分着吃也比较自然，不会像特别甜腻的零食那样有负担。",
            "如果你也想囤一点早餐、下午茶都能吃的小点心，可以先从这种日常场景试试。{detail}",
        ],
        "summary_sentence": "{name}适合早餐和下午茶场景。",
    },
    "美妆护肤": {
        "fallback": "这款小东西",
        "title_patterns": [
            "{name}，最近出门都会带",
            "最近用下来，{name}肤感还挺舒服",
            "日常护肤里，我会留下{name}",
            "不厚重，通勤用{name}刚好",
            "空瓶前想认真说说{name}",
        ],
        "selling_points": [
            "质地不会太厚重",
            "通勤用起来顺手",
            "肤感比较舒服",
            "包装方便随身带",
            "适合日常护理",
        ],
        "focus": ["质地舒服", "肤感清爽", "日常护理很顺手"],
        "titles": ["最近常用的", "通勤也适合的", "肤感挺舒服的", "日常护理会用到的", "想空瓶回购的"],
        "hashtags": ["#护肤分享", "#美妆好物", "#空瓶回购", "#日常护肤", "#通勤好物", "#护肤日常", "#真实测评"],
        "suitable_for": "喜欢日常护肤和通勤好物的人",
        "recommend_reason": "质地舒服、肤感清爽、日常护理顺手",
        "comments": ["你更在意质地还是肤感？", "这类护肤好物你会想试试吗？", "还想看哪些日常护理分享？"],
        "body": [
            "最近出门和通勤时常会带着{name}，用下来属于不太有负担的日常型小物。",
            "我比较在意质地和肤感，它不会显得很厚重，日常补用也还算顺手。包装携带起来也方便，不需要专门腾很大空间。",
            "更适合想把护理步骤做简单一点的人参考；如果你偏爱特别强存在感的使用体验，可能需要再对比看看。{detail}",
        ],
        "summary_sentence": "{name}更适合日常护理场景。",
    },
    "家居日用": {
        "fallback": "这个好物",
        "title_patterns": [
            "{name}，用过才知道方便",
            "最近家里最常用的小东西：{name}",
            "不起眼，但{name}真的提升日常效率",
            "适合懒人整理的小工具{name}",
            "{name}比想象中实用",
        ],
        "selling_points": [
            "不占太多地方",
            "用起来省事",
            "小空间也能用",
            "收纳清洁更方便",
            "日常使用频率高",
        ],
        "focus": ["日常实用", "收纳清洁更顺手", "质感在线"],
        "titles": ["让日常更顺手的", "家里用着很方便的", "提升生活感的", "实用感不错的", "最近很常用的"],
        "hashtags": ["#家居好物", "#生活好物", "#收纳整理", "#日用分享", "#实用好物", "#居家日常", "#好物分享"],
        "suitable_for": "喜欢实用家居和日用分享的人",
        "recommend_reason": "实用、方便、能让日常更顺手",
        "comments": ["你家里最需要哪类日用好物？", "这类实用分享你想继续看吗？", "你更喜欢收纳还是清洁类好物？"],
        "body": [
            "最近家里用得比较频繁的是{name}，它不是很夸张的东西，但放进日常之后确实更顺手。",
            "使用场景主要是收纳、清洁或随手整理，用起来省事，也不太占地方。对小空间来说，这种不需要复杂操作的小物会更友好。",
            "适合想让家里日常效率高一点的人；如果你更在意外观装饰感，可以再看看颜色和摆放位置。{detail}",
        ],
        "summary_sentence": "{name}适合高频日用场景。",
    },
    "母婴儿童": {
        "fallback": "这件小东西",
        "title_patterns": [
            "{name}，带娃日常会用到",
            "亲子生活里，{name}还挺方便",
            "外出也顺手的{name}",
            "孩子日常可以参考{name}",
            "宝妈可以看看{name}这个小物",
        ],
        "selling_points": [
            "日常使用方便",
            "外出携带顺手",
            "收纳不太费心",
            "亲子场景能用",
            "带娃日常更省事",
        ],
        "focus": ["日常使用方便", "外出携带顺手", "亲子场景适合"],
        "titles": ["带娃日常会用到的", "亲子生活里挺方便的", "外出也顺手的", "孩子日常适合的", "宝妈可以参考的"],
        "hashtags": ["#母婴好物", "#育儿日常", "#亲子生活", "#带娃日常", "#宝妈分享", "#母婴分享", "#好物分享"],
        "suitable_for": "关注亲子生活和带娃日常的人",
        "recommend_reason": "日常使用方便，外出或收纳都比较顺手",
        "comments": ["带娃日常你最需要哪类好物？", "你会关注方便携带这一点吗？", "还想看哪些亲子生活分享？"],
        "body": [
            "最近在亲子日常里会用到{name}，整体感受是比较方便，不需要额外花很多时间适应。",
            "它更适合外出、收纳或家里随手使用的场景，能让一些小流程轻松一点。对带娃日常来说，省心和顺手会比花哨功能更重要。",
            "适合想减少琐碎操作的人参考；具体是否适合自家情况，还是建议结合年龄、使用场景和习惯判断。{detail}",
        ],
        "summary_sentence": "{name}适合亲子日常小场景。",
    },
    "宠物用品": {
        "fallback": "这个宠物小物",
        "title_patterns": [
            "最近给猫咪用的{name}，还挺省心",
            "养宠日常里，{name}算实用的",
            "给毛孩子准备的日常小物{name}",
            "最近回购的宠物用品之一：{name}",
            "养宠人可以看看{name}",
        ],
        "selling_points": [
            "养宠日常更省心",
            "拿取收纳方便",
            "适合日常囤一点",
            "清洁护理更顺手",
            "适合家里常备",
        ],
        "focus": ["日常照顾方便", "适口性友好", "适合囤货"],
        "titles": ["养宠日常会用到的", "猫狗日常挺方便的", "适合家里备一点的", "最近觉得顺手的", "养宠人可以参考的"],
        "hashtags": ["#宠物用品", "#养宠好物", "#猫咪日常", "#狗狗日常", "#宠物日常", "#养宠分享", "#好物分享"],
        "suitable_for": "关注宠物日常照顾的人",
        "recommend_reason": "方便照顾，日常使用和囤货都比较省心",
        "comments": ["你家宠物更挑哪一点？", "养宠日常你最想省心的是什么？", "还想看哪些宠物用品分享？"],
        "body": [
            "最近养宠日常里用到{name}，它给我的第一感受是比较省心，拿取和收纳都不麻烦。",
            "这类用品最重要的不是多复杂，而是能不能稳定融入日常照顾。无论是清洁、护理还是喂养相关场景，顺手就会加分很多。",
            "适合家里常备或想减少琐碎步骤的养宠人参考；不同宠物习惯不一样，建议先看自家毛孩子的接受度。{detail}",
        ],
        "summary_sentence": "{name}适合养宠日常常备。",
    },
    "服饰配件": {
        "fallback": "这件小东西",
        "title_patterns": [
            "{name}，日常搭配很顺手",
            "通勤也能用的{name}",
            "{name}的质感挺加分",
            "最近常搭的配饰：{name}",
            "想让穿搭更省心，可以看看{name}",
        ],
        "selling_points": [
            "日常好搭",
            "通勤也能用",
            "舒适度还不错",
            "质感比较加分",
            "不挑搭配场景",
        ],
        "focus": ["日常好搭", "通勤舒服", "质感显气质"],
        "titles": ["日常搭配很顺手的", "通勤也能用的", "质感挺加分的", "最近常搭的", "显气质的小配件"],
        "hashtags": ["#穿搭分享", "#配饰分享", "#通勤穿搭", "#日常穿搭", "#质感穿搭", "#好物分享", "#搭配灵感"],
        "suitable_for": "喜欢日常穿搭和通勤搭配的人",
        "recommend_reason": "好搭、舒服、能给日常造型加一点质感",
        "comments": ["你更喜欢通勤风还是休闲风？", "这类搭配你会想试试吗？", "还想看哪些配饰分享？"],
        "body": [
            "最近搭配里经常出现{name}，它属于不抢戏但能增加细节感的类型。",
            "日常和通勤都能用，搭配起来不需要花太多心思。质感、舒适度和使用频率都还算平衡，不会只适合拍照。",
            "适合想让穿搭更省心的人参考；如果你喜欢很强风格感的单品，可能需要搭配更多衣服再判断。{detail}",
        ],
        "summary_sentence": "{name}适合日常搭配场景。",
    },
    "其他好物": {
        "fallback": "这个好物",
        "title_patterns": [
            "{name}，用起来比想象中顺手",
            "最近会反复用到{name}",
            "不挑场景的日常小东西{name}",
            "{name}适合轻松分享一下",
            "这个{name}，比想象中实用",
        ],
        "selling_points": [
            "用起来顺手",
            "不挑使用场景",
            "日常使用频率高",
            "适合轻分享",
            "比想象中实用",
        ],
        "focus": ["日常好用", "方便顺手", "质感舒服"],
        "titles": ["真的很适合日常的", "最近很喜欢的", "让我觉得省心的", "很值得试试的", "想认真分享的"],
        "hashtags": ["#好物分享", "#日常好物", "#小红书种草", "#真实体验", "#好物推荐", "#生活好物", "#好用分享"],
        "suitable_for": "喜欢日常好物分享的人",
        "recommend_reason": "好用、方便、让日常更轻松",
        "comments": ["你平时最在意哪一点？", "如果你也想看更多实用分享，我可以继续整理", "这类好物你会不会想试试？"],
        "body": [
            "最近用到{name}的次数比想象中多，它不是特别复杂的东西，但日常里确实挺顺手。",
            "我比较喜欢它不挑场景，随手用、随手放都不会有太多负担。对普通日常来说，这种使用频率高的小物反而更容易留下来。",
            "适合想找一个轻松提升日常体验的人参考；如果你追求很专业或很强功能的产品，可能还需要再对比。{detail}",
        ],
        "summary_sentence": "{name}适合轻松放进日常。",
    },
}

CATEGORY_ALIASES = {
    "食品": "食品饮品",
    "饮品": "食品饮品",
    "零食": "食品饮品",
    "美妆": "美妆护肤",
    "护肤": "美妆护肤",
    "家居": "家居日用",
    "日用": "家居日用",
    "母婴": "母婴儿童",
    "儿童": "母婴儿童",
    "宠物": "宠物用品",
    "服饰": "服饰配件",
    "配件": "服饰配件",
}

CATEGORY_KEYWORDS = {
    "食品饮品": ["蛋糕", "早餐", "下午茶", "口感", "软", "零食", "饮品", "牛奶", "咖啡", "茶", "饼干", "面包"],
    "美妆护肤": ["护手霜", "面霜", "精华", "口红", "粉底", "护肤", "肤感", "质地"],
    "家居日用": ["收纳", "清洁", "家里", "厨房", "卫生间", "整理", "日用"],
    "宠物用品": ["猫", "狗", "宠物", "毛孩子", "猫咪", "狗狗"],
}

STYLE_COPY = {
    "清新简约": {
        "cover_suffix": "真实分享",
        "summary_pattern": "关于{name}，我想说这几点",
    },
    "可爱手账": {
        "cover_suffix": "今日小分享",
        "summary_pattern": "{name}的日常小发现",
    },
    "生活方式": {
        "cover_suffix": "日常好物",
        "summary_pattern": "{name}适合这些场景",
    },
    "干货清单": {
        "cover_suffix": "这几点值得看",
        "summary_pattern": "{name}的 3 个体验点",
    },
    "温柔日常": {
        "cover_suffix": "温柔日常分享",
        "summary_pattern": "慢慢用下来，{name}还不错",
    },
}


def _safe_text(value: str, fallback: str) -> str:
    cleaned = "".join(ch for ch in value.strip() if ch not in ["\n", "\r", "\t"])
    return cleaned or fallback


def _unique(items: Iterable[str], limit: int | None = None) -> list[str]:
    result = []
    seen = set()
    for item in items:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
        if limit and len(result) >= limit:
            break
    return result


def _clip_unique(items: Iterable[str], max_len: int, limit: int | None = None) -> list[str]:
    return _unique((item[:max_len] for item in items), limit=limit)


def _resolve_category(category: str, product_name: str, description: str) -> str:
    category_text = (category or "").strip()
    if category_text in CATEGORY_TEMPLATES and category_text != "其他好物":
        return category_text

    for keyword, category_value in CATEGORY_ALIASES.items():
        if keyword in category_text:
            return category_value

    combined_text = f"{product_name} {description}"
    for category_value, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in combined_text for keyword in keywords):
            return category_value

    return "其他好物"


def generate_note_payload(
    description: str,
    content_type: str,
    style: str,
    product_name: str = "",
    category: str = "其他好物",
) -> Dict[str, object]:
    category_value = _resolve_category(category, product_name, description)
    template = CATEGORY_TEMPLATES[category_value]
    product_value = _safe_text(product_name, template.get("fallback", "这个好物"))
    description_value = _safe_text(description, "")
    content_type_value = _safe_text(content_type, "好物推荐")
    style_value = _safe_text(style, "清新简约")
    style_copy = STYLE_COPY.get(style_value, STYLE_COPY["清新简约"])

    display_name = product_value[:12]
    detail_hint = f"补充一下我的使用感受：{description_value}" if description_value else ""

    title_patterns = template.get("title_patterns", [])
    if title_patterns:
        note_titles = _unique((pattern.format(name=display_name) for pattern in title_patterns), limit=5)
    else:
        title_directions = template["titles"]
        note_titles = _unique(
            [
                f"{display_name}，{title_directions[0]}",
                f"最近喜欢的{display_name}",
                f"{title_directions[1]}{display_name}",
                f"{display_name}真实分享：{title_directions[2]}",
                f"不夸张，{display_name}我会继续用",
            ],
            limit=5,
        )

    selling_pool = template.get("selling_points", template["focus"])
    selling_points = _clip_unique(selling_pool, 20, limit=3)

    cover_title = f"{display_name}，{style_copy['cover_suffix']}"
    if len(cover_title) > 18:
        cover_title = cover_title[:18]

    cover_subtitle = f"{category_value}｜{content_type_value}｜{style_value}"
    if len(cover_subtitle) > 20:
        cover_subtitle = cover_subtitle[:20]

    summary_sentence = template.get("summary_sentence", f"如果你也在看{display_name}，这款可以作为日常参考。").format(name=display_name)
    if len(summary_sentence) > 40:
        summary_sentence = summary_sentence[:40]

    hashtags = _unique([*template["hashtags"], "#真实体验", "#种草笔记"], limit=10)
    body_template = template["body"]
    if isinstance(body_template, list):
        note_body = "".join(body_template).format(name=product_value, detail=detail_hint)
    else:
        note_body = body_template.format(name=product_value) + (f" {detail_hint}" if detail_hint else "")

    return {
        "cover_title": cover_title,
        "cover_subtitle": cover_subtitle,
        "selling_points": selling_points,
        "summary_title": style_copy["summary_pattern"].format(name=display_name)[:24],
        "suitable_for": template["suitable_for"],
        "recommend_reason": template["recommend_reason"],
        "summary_sentence": summary_sentence,
        "note_titles": note_titles,
        "note_body": note_body,
        "hashtags": hashtags,
        "comments": template["comments"],
        "product_name": product_value,
        "category": category_value,
    }
