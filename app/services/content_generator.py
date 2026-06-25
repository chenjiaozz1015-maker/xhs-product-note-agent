from __future__ import annotations

from typing import Dict, List


def generate_note_payload(description: str, content_type: str, style: str) -> Dict[str, object]:
    description_value = description.strip() or "这件好物"
    content_type_value = content_type or "好物推荐"
    style_value = style or "清新简约"

    selling_points = [
        f"{description_value}的日常好用感",
        "外观和质感都很舒服",
        "适合日常轻松使用",
    ]

    note_titles = [
        f"{description_value}真的很值得入手",
        f"我最近很喜欢这个{description_value}",
        f"分享一个让我省心的{description_value}",
        f"这款{description_value}，真的很适合日常",
        f"不太会推荐，但这个{description_value}我很喜欢",
    ]

    return {
        "cover_title": f"{description_value}，我真的想安利给你",
        "cover_subtitle": f"{content_type_value}｜{style_value}｜一眼就想收藏",
        "selling_points": selling_points,
        "summary_title": f"关于{description_value}，我想说这几点",
        "suitable_for": "喜欢日常好物分享的人",
        "recommend_reason": "好看、好用、让日常变得轻松一些",
        "summary_sentence": f"如果你也在找一个日常好用的{description_value}，这款很值得试试。",
        "note_titles": note_titles,
        "note_body": (
            f"最近一直在用{description_value}，真的没有想到它会这么顺手。"
            f"平时的使用感受还不错，整体看起来很舒服，带出去或者在家里用都挺方便。"
            f"如果你也想找一个日常里能省心一点的好物，这个很值得留意。"
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
