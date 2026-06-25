from __future__ import annotations

from typing import Dict


def _safe_text(value: str, fallback: str) -> str:
    cleaned = "".join(ch for ch in value.strip() if ch not in ["\n", "\r", "\t"])
    return cleaned or fallback


def generate_note_payload(description: str, content_type: str, style: str) -> Dict[str, object]:
    description_value = _safe_text(description, "这件好物")
    content_type_value = _safe_text(content_type, "好物推荐")
    style_value = _safe_text(style, "清新简约")

    if len(description_value) > 10:
        short_description = description_value[:10]
    else:
        short_description = description_value

    selling_points = [
        f"{short_description}的日常好用感",
        "质感和使用感都很顺手",
        "很适合日常轻松分享",
    ]

    note_titles = [
        f"{short_description}真的很适合日常",
        f"我最近很喜欢这个{short_description}",
        f"分享一个让我觉得省心的{short_description}",
        f"这款{short_description}，很值得试试",
        f"不太会推荐，但这个{short_description}我挺喜欢",
    ]

    cover_title = f"{short_description}，我想认真说说"
    if len(cover_title) > 18:
        cover_title = cover_title[:18]

    cover_subtitle = f"{content_type_value}｜{style_value}"
    if len(cover_subtitle) > 20:
        cover_subtitle = cover_subtitle[:20]

    summary_sentence = f"如果你也想找一个日常里好用一点的{short_description}，这款很值得试试。"
    if len(summary_sentence) > 40:
        summary_sentence = summary_sentence[:40]

    return {
        "cover_title": cover_title,
        "cover_subtitle": cover_subtitle,
        "selling_points": [point[:20] for point in selling_points],
        "summary_title": f"关于{short_description}，我想说这几点",
        "suitable_for": "喜欢日常好物分享的人",
        "recommend_reason": "好看、好用、让日常更轻松",
        "summary_sentence": summary_sentence,
        "note_titles": note_titles,
        "note_body": (
            f"最近一直在用{short_description}，整体体验还挺顺手的。"
            f"它的样子和使用感都比较舒服，日常带着或者在家里用都很方便。"
            f"如果你也在找一个不想太复杂、但又想有点好用感觉的好物，这个很值得看看。"
        ),
        "hashtags": [
            "#好物分享",
            "#日常好物",
            "#小红书种草",
            "#真实体验",
            "#好物推荐",
            "#生活好物",
            "#好用分享",
            "#小众好物",
            "#实用分享",
            "#种草笔记",
        ],
        "comments": [
            "你平时最在意哪一点？",
            "如果你也想看更多实用分享，我可以继续整理",
            "这类好物你会不会想试试？",
        ],
    }
