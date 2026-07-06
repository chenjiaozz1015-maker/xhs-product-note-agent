from __future__ import annotations

from typing import Dict, Iterable

from app.services.category_profile import detect_product_profile, get_profile_copy


STYLE_COPY = {
    "清新简约": {"cover_suffix": "真实分享", "summary_pattern": "关于{name}，我想说这几点"},
    "可爱手账": {"cover_suffix": "今日小分享", "summary_pattern": "{name}的日常小发现"},
    "生活方式": {"cover_suffix": "日常好物", "summary_pattern": "{name}适合这些场景"},
    "干货清单": {"cover_suffix": "这几点值得看", "summary_pattern": "{name}的 3 个体验点"},
    "温柔日常": {"cover_suffix": "温柔日常分享", "summary_pattern": "慢慢用下来，{name}还不错"},
}

FALLBACK_NAMES = {
    "food": "这个小点心",
    "beauty": "这个护理好物",
    "home": "这个日用好物",
    "pet": "这个宠物好物",
    "other": "这个好物",
}


FORBIDDEN_TITLE_WORDS = ["必买", "最强", "神器", "全网第一", "暴瘦", "燃脂", "减重神器"]


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


def _pick_variant(options: list[str], seed_text: str, fallback: str) -> str:
    if not options:
        return fallback
    index = sum(ord(ch) for ch in seed_text) % len(options)
    return options[index]


def _sanitize_titles(titles: Iterable[str], limit: int = 5) -> list[str]:
    cleaned = []
    for title in titles:
        value = title[:18].strip("，。！! ")
        if not value or any(word in value for word in FORBIDDEN_TITLE_WORDS):
            continue
        cleaned.append(value)
    return _unique(cleaned, limit=limit)


def generate_note_payload(
    description: str,
    content_type: str,
    style: str,
    product_name: str = "",
    category: str = "其他好物",
) -> Dict[str, object]:
    content_type_value = _safe_text(content_type, "好物推荐")
    style_value = _safe_text(style, "清新简约")
    profile = detect_product_profile(product_name, category, description)
    profile_copy = get_profile_copy(profile)
    product_value = _safe_text(product_name, FALLBACK_NAMES.get(profile.main_category, "这个好物"))
    description_value = _safe_text(description, "")
    style_copy = STYLE_COPY.get(style_value, STYLE_COPY["清新简约"])
    display_name = product_value[:12]
    detail_hint = f"补充一下我的使用感受：{description_value}" if description_value else ""
    seed_text = f"{display_name}|{style_value}|{content_type_value}|{profile.sub_category}|{description_value}"

    note_titles = _sanitize_titles(
        pattern.format(name=display_name) for pattern in profile_copy.get("title_patterns", [])
    )
    if len(note_titles) < 5:
        note_titles = _sanitize_titles([
            *note_titles,
            f"{display_name}，{style_copy['cover_suffix']}",
            f"最近会反复用到的{display_name}",
            f"{display_name}，更适合日常分享",
            f"想认真聊聊{display_name}",
            f"{display_name}这类我会继续用",
        ])

    selling_points = _clip_unique(profile_copy.get("selling_points", []), 20, limit=3)
    hashtags = _unique([*profile_copy.get("hashtags", []), "#真实体验", "#种草笔记"], limit=10)
    comments = _unique(profile_copy.get("comments", []), limit=3)

    body_pattern = _pick_variant(profile_copy.get("body_patterns", []), seed_text, f"最近会反复用到{product_value}，它更适合放进真实日常场景里去分享。{detail_hint}")
    note_body = body_pattern.format(name=product_value, detail=detail_hint)

    suitable_for = profile_copy.get("suitable_for", "喜欢日常分享的人")
    recommend_reason = profile_copy.get("recommend_reason", "更适合放进真实日常场景里去分享")
    summary_sentence = profile_copy.get("summary_sentence", f"{display_name}适合放进真实日常场景里。")
    summary_sentence = summary_sentence.format(name=display_name)[:40]

    cover_title = f"{display_name}，{style_copy['cover_suffix']}"[:18]
    cover_subtitle = f"{profile.category_label}｜{content_type_value}｜{style_value}"[:20]
    summary_title = style_copy["summary_pattern"].format(name=display_name)[:24]

    return {
        "cover_title": cover_title,
        "cover_subtitle": cover_subtitle,
        "selling_points": selling_points,
        "summary_title": summary_title,
        "suitable_for": suitable_for,
        "recommend_reason": recommend_reason,
        "summary_sentence": summary_sentence,
        "note_titles": note_titles[:5],
        "note_body": note_body,
        "hashtags": hashtags,
        "comments": comments,
        "product_name": product_value,
        "category": profile.category_label,
        "sub_category": profile.sub_category,
        "profile_keywords": list(profile.keywords),
        "tone_tags": list(profile.tone_tags),
    }
