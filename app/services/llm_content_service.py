"""LLM content service.

`openai_compatible` here means a service that speaks the OpenAI-style chat
completion protocol. It is intentionally provider-agnostic and can be wired to
compatible domestic platforms through environment variables such as
`LLM_BASE_URL`, `LLM_MODEL`, and `LLM_API_KEY`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any
from urllib import error, request
from urllib.parse import urlparse

from app.config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MAX_RETRIES,
    LLM_MODEL,
    LLM_PROVIDER,
    LLM_TIMEOUT_SECONDS,
)
from app.services.category_profile import detect_product_profile, get_profile_copy


MAX_TITLE_LENGTH = 18
MAX_BODY_LENGTH = 220
MAX_COMMENT_LENGTH = 32
MAX_SUMMARY_LENGTH = 40
MAX_SELLING_POINT_LENGTH = 20
MAX_REASON_LENGTH = 28
MAX_SUITABLE_FOR_LENGTH = 18
SYSTEM_COPY_FORBIDDEN = (
    "可直接复制发布",
    "可直接编辑后发布",
    "可复制发布",
    "发布说明",
    "生成后可修改",
    "系统提示",
)


@dataclass(frozen=True)
class LLMContentResult:
    success: bool
    note_data: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None


def _strip_text(value: Any) -> str:
    return str(value or "").replace("\r", " ").replace("\n", " ").strip()


def _truncate(value: str, limit: int) -> str:
    return _strip_text(value)[:limit].strip("，。；;、 ")


def _unique_texts(values: list[str], limit: int | None = None) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = _strip_text(value)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
        if limit and len(result) >= limit:
            break
    return result


def _normalize_hashtags(values: Any) -> list[str]:
    if isinstance(values, str):
        candidates = values.replace("，", " ").replace(",", " ").split()
    elif isinstance(values, list):
        candidates = [_strip_text(item) for item in values]
    else:
        candidates = []

    normalized = []
    for item in candidates:
        cleaned = item.lstrip("#").strip()
        if not cleaned:
            continue
        normalized.append(f"#{cleaned[:18]}")
    return _unique_texts(normalized, limit=12)


def _normalize_comments(values: Any) -> list[str]:
    if isinstance(values, str):
        candidates = [values]
    elif isinstance(values, list):
        candidates = [_strip_text(item) for item in values]
    else:
        candidates = []
    return _unique_texts([_truncate(item, MAX_COMMENT_LENGTH) for item in candidates], limit=5)


def _normalize_titles(values: Any) -> list[str]:
    if isinstance(values, str):
        candidates = [values]
    elif isinstance(values, list):
        candidates = [_strip_text(item) for item in values]
    else:
        candidates = []
    return _unique_texts([_truncate(item, MAX_TITLE_LENGTH) for item in candidates], limit=5)


def _normalize_selling_points(values: Any) -> list[str]:
    candidates: list[str] = []
    if isinstance(values, list):
        for item in values:
            if isinstance(item, dict):
                title = _strip_text(item.get("title"))
                description = _strip_text(item.get("description"))
                combined = title or description
                if title and description and description not in title:
                    combined = f"{title} {description}"
                candidates.append(combined)
            else:
                candidates.append(_strip_text(item))
    elif isinstance(values, str):
        candidates = [values]
    return _unique_texts([_truncate(item, MAX_SELLING_POINT_LENGTH) for item in candidates], limit=3)


def _extract_json_string(content: str) -> str:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        lines = [line for line in cleaned.splitlines() if not line.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()
    return cleaned


def _extract_message_content(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(_strip_text(item.get("text") or item.get("content")))
            else:
                parts.append(_strip_text(item))
        return "\n".join(part for part in parts if part).strip()
    return _strip_text(content)


def _resolve_base_url(base_url: str) -> str:
    cleaned = base_url.strip()
    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    if cleaned.endswith("/chat/completions"):
        return cleaned
    return f"{cleaned.rstrip('/')}/chat/completions"


def _build_messages(content_input: Any) -> list[dict[str, str]]:
    profile = content_input.category_profile
    if profile is None:
        detected_profile = detect_product_profile(
            content_input.product_name,
            content_input.category,
            content_input.description,
        )
        profile = {
            "main_category": detected_profile.main_category,
            "sub_category": detected_profile.sub_category,
            "category_label": detected_profile.category_label,
            "keywords": list(detected_profile.keywords),
            "tone_tags": list(detected_profile.tone_tags),
            "copy": get_profile_copy(detected_profile),
        }

    copy_config = profile.get("copy", {}) if isinstance(profile, dict) else {}
    main_category = profile.get("main_category", "") if isinstance(profile, dict) else ""
    sub_category = profile.get("sub_category", "") if isinstance(profile, dict) else ""
    category_label = profile.get("category_label", content_input.category) if isinstance(profile, dict) else content_input.category
    tone_tags = profile.get("tone_tags", []) if isinstance(profile, dict) else []
    matched_keywords = profile.get("keywords", []) if isinstance(profile, dict) else []
    banned_word_hints = {
        "food": "避免出现护肤、收纳、清洁、功能产品、小物、随手用。",
        "beauty": "避免出现早餐、下午茶、收纳、厨房、浴室。",
        "home": "避免出现减肥、护肤功效、早餐口感等错类目表达。",
        "pet": "避免出现上妆、早餐、护肤等错类目表达。",
    }
    user_prompt = f"""
请基于以下商品信息生成小红书风格发布文案，输出严格 JSON，不要输出解释文字。

商品名称：{content_input.product_name or "未填写"}
商品类目：{content_input.category}
细分类目：{sub_category}
类目标签：{category_label}
商品描述：{content_input.description or "未填写"}
内容类型：{content_input.content_type}
风格：{content_input.style}
匹配关键词：{", ".join(matched_keywords) or "无"}
风格/语气标签：{", ".join(tone_tags) or "无"}
类目参考卖点：{", ".join(copy_config.get("selling_points", [])[:5]) or "无"}
类目参考标签：{", ".join(copy_config.get("hashtags", [])[:6]) or "无"}

要求：
1. 不要写系统提示文案，例如“可直接复制发布”“可编辑后发布”。
2. 不要写医疗、减肥、保证效果、全网第一、最强、神器这类表达。
3. 文案必须贴合商品类目，{banned_word_hints.get(main_category, "避免错类目表达。")}
4. 标题适合小红书，简短自然，不要过度营销。
5. hashtag 保持短词，可不带 #，系统会补齐。
6. 卖点可以写成短标题，或 title + description 结构。

请返回 JSON，字段格式如下：
{{
  "titles": ["标题1", "标题2", "标题3"],
  "body": "正文内容",
  "hashtags": ["标签1", "标签2"],
  "comment_prompts": ["评论引导1", "评论引导2"],
  "selling_points": [
    {{"title": "卖点1", "description": "一句说明"}},
    {{"title": "卖点2", "description": "一句说明"}},
    {{"title": "卖点3", "description": "一句说明"}}
  ],
  "summary_title": "总结标题",
  "suitable_for": "适合谁",
  "recommend_reason": "推荐理由",
  "summary_sentence": "一句总结"
}}
""".strip()
    return [
        {
            "role": "system",
            "content": (
                "你是中文小红书种草文案助手。"
                "你只输出合法 JSON，不输出 markdown，不输出解释。"
            ),
        },
        {"role": "user", "content": user_prompt},
    ]


def _normalize_note_data(raw_data: dict[str, Any], fallback_note_data: dict[str, Any]) -> dict[str, Any] | None:
    titles = _normalize_titles(raw_data.get("titles") or raw_data.get("note_titles"))
    body = _truncate(raw_data.get("body") or raw_data.get("note_body") or "", MAX_BODY_LENGTH)
    hashtags = _normalize_hashtags(raw_data.get("hashtags"))
    comments = _normalize_comments(raw_data.get("comment_prompts") or raw_data.get("comments"))
    selling_points = _normalize_selling_points(raw_data.get("selling_points"))

    if not titles or not body or len(hashtags) < 2 or len(comments) < 1 or len(selling_points) < 3:
        return None
    if any(copy in body for copy in SYSTEM_COPY_FORBIDDEN):
        return None

    note_data = dict(fallback_note_data)
    note_data["note_titles"] = titles
    note_data["note_body"] = body
    note_data["hashtags"] = hashtags
    note_data["comments"] = comments
    note_data["selling_points"] = selling_points

    cover_title = _truncate(raw_data.get("cover_title") or titles[0], MAX_TITLE_LENGTH)
    if cover_title:
        note_data["cover_title"] = cover_title

    cover_subtitle = _truncate(raw_data.get("cover_subtitle") or note_data.get("cover_subtitle", ""), 20)
    if cover_subtitle:
        note_data["cover_subtitle"] = cover_subtitle

    summary_title = _truncate(raw_data.get("summary_title") or note_data.get("summary_title", ""), 24)
    if summary_title:
        note_data["summary_title"] = summary_title

    suitable_for = _truncate(raw_data.get("suitable_for") or note_data.get("suitable_for", ""), MAX_SUITABLE_FOR_LENGTH)
    if suitable_for:
        note_data["suitable_for"] = suitable_for

    recommend_reason = _truncate(raw_data.get("recommend_reason") or note_data.get("recommend_reason", ""), MAX_REASON_LENGTH)
    if recommend_reason:
        note_data["recommend_reason"] = recommend_reason

    summary_sentence = _truncate(raw_data.get("summary_sentence") or note_data.get("summary_sentence", ""), MAX_SUMMARY_LENGTH)
    if summary_sentence:
        note_data["summary_sentence"] = summary_sentence

    return note_data


def _post_chat_completion(
    endpoint: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout_seconds: float,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request_obj = request.Request(endpoint, data=body, headers=headers, method="POST")
    with request.urlopen(request_obj, timeout=timeout_seconds) as response:
        raw = response.read().decode("utf-8")
    return json.loads(raw)


def generate_openai_compatible_note_data(
    content_input: Any,
    fallback_note_data: dict[str, Any],
) -> LLMContentResult:
    if LLM_PROVIDER != "openai_compatible":
        return LLMContentResult(success=False, error_message=f"当前 LLM_PROVIDER={LLM_PROVIDER}，暂不支持。")
    if not LLM_API_KEY:
        return LLMContentResult(success=False, error_message="未配置 LLM_API_KEY，已 fallback 到 rule_based。")
    if not LLM_MODEL:
        return LLMContentResult(success=False, error_message="未配置 LLM_MODEL，已 fallback 到 rule_based。")

    endpoint = _resolve_base_url(LLM_BASE_URL)
    if not endpoint:
        return LLMContentResult(success=False, error_message="LLM_BASE_URL 无效，已 fallback 到 rule_based。")

    request_payload = {
        "model": LLM_MODEL,
        "messages": _build_messages(content_input),
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    last_error = "LLM 调用失败，已 fallback 到 rule_based。"
    for _ in range(LLM_MAX_RETRIES + 1):
        try:
            response_payload = _post_chat_completion(
                endpoint=endpoint,
                payload=request_payload,
                headers=headers,
                timeout_seconds=LLM_TIMEOUT_SECONDS,
            )
            content = _extract_message_content(response_payload)
            if not content:
                last_error = "LLM 返回为空，已 fallback 到 rule_based。"
                continue
            raw_data = json.loads(_extract_json_string(content))
            if not isinstance(raw_data, dict):
                last_error = "LLM JSON 结构无效，已 fallback 到 rule_based。"
                continue
            note_data = _normalize_note_data(raw_data, fallback_note_data)
            if not note_data:
                last_error = "LLM 返回字段不完整或不符合格式，已 fallback 到 rule_based。"
                continue
            return LLMContentResult(success=True, note_data=note_data)
        except (error.URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
            last_error = f"LLM 调用异常：{exc}，已 fallback 到 rule_based。"
        except Exception as exc:  # pragma: no cover
            last_error = f"LLM 未知异常：{exc}，已 fallback 到 rule_based。"

    return LLMContentResult(success=False, error_message=last_error)
