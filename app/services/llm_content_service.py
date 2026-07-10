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
    CONTENT_ENGINE_TYPE,
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MAX_RETRIES,
    LLM_MAX_RETRIES_RAW,
    LLM_MODEL,
    LLM_PROVIDER,
    LLM_TIMEOUT_SECONDS,
    LLM_TIMEOUT_SECONDS_RAW,
)
from app.services.category_profile import detect_product_profile, get_profile_copy
from app.services.runtime_config_service import get_runtime_config_values


SUPPORTED_CONTENT_ENGINE_TYPES = {
    "rule_based",
    "llm_placeholder",
    "llm_openai_compatible",
}
MAX_TITLE_LENGTH = 24
MAX_BODY_LENGTH = 180
MAX_COMMENT_LENGTH = 32
MAX_SUMMARY_LENGTH = 40
MAX_SELLING_POINT_LENGTH = 18
MAX_REASON_LENGTH = 28
MAX_SUITABLE_FOR_LENGTH = 18
MAX_HASHTAGS = 8
MAX_TITLES = 5
MIN_TITLES = 3
REQUIRED_SELLING_POINTS = 3
SYSTEM_COPY_FORBIDDEN = (
    "可直接复制发布",
    "可直接编辑后发布",
    "可复制发布",
    "发布说明",
    "生成后可修改",
    "系统提示",
)


@dataclass(frozen=True)
class LLMConfigStatus:
    requested_engine_type: str
    resolved_engine_type: str
    llm_provider: str
    llm_config_ready: bool
    status_code: str
    missing_fields: tuple[str, ...] = ()
    invalid_fields: tuple[str, ...] = ()
    llm_base_url_status: str = "missing"
    llm_model_status: str = "missing"
    llm_api_key_status: str = "missing"
    llm_api_key_preview: str = "missing"
    timeout_seconds: float = 15.0
    max_retries: int = 1
    llm_provider_source: str = "default"
    llm_base_url_source: str = "missing"
    llm_model_source: str = "missing"
    llm_api_key_source: str = "missing"
    llm_timeout_seconds_source: str = "default"
    llm_max_retries_source: str = "default"


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


def _mask_api_key(api_key: str) -> str:
    cleaned = api_key.strip()
    if not cleaned:
        return "missing"
    if len(cleaned) <= 8:
        return "configured"
    return f"{cleaned[:2]}-****{cleaned[-4:]}"


def _safe_float(value: str, default: float = 15.0) -> tuple[float, bool]:
    try:
        return float(value), True
    except (TypeError, ValueError):
        return default, False


def _safe_int(value: str, default: int = 1) -> tuple[int, bool]:
    try:
        return int(value), True
    except (TypeError, ValueError):
        return default, False


def _resolve_base_url(base_url: str) -> str:
    cleaned = base_url.strip()
    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    if cleaned.endswith("/chat/completions"):
        return cleaned
    return f"{cleaned.rstrip('/')}/chat/completions"


def get_llm_config_status(
    content_engine_type: str | None = None,
    llm_provider: str | None = None,
    llm_api_key: str | None = None,
    llm_base_url: str | None = None,
    llm_model: str | None = None,
    llm_timeout_seconds_raw: str | None = None,
    llm_max_retries_raw: str | None = None,
) -> LLMConfigStatus:
    content_engine_setting = (
        {"value": content_engine_type}
        if content_engine_type is not None
        else get_runtime_config_values(
            ["CONTENT_ENGINE_TYPE"], {"CONTENT_ENGINE_TYPE": CONTENT_ENGINE_TYPE}
        )["CONTENT_ENGINE_TYPE"]
    )
    requested_engine_type = str(content_engine_setting.get("value") or "rule_based").strip() or "rule_based"
    resolved = get_runtime_config_values(
        ["LLM_PROVIDER", "LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL", "LLM_TIMEOUT_SECONDS", "LLM_MAX_RETRIES"],
        defaults={
            "LLM_PROVIDER": LLM_PROVIDER,
            "LLM_API_KEY": LLM_API_KEY,
            "LLM_BASE_URL": LLM_BASE_URL,
            "LLM_MODEL": LLM_MODEL,
            "LLM_TIMEOUT_SECONDS": LLM_TIMEOUT_SECONDS_RAW,
            "LLM_MAX_RETRIES": LLM_MAX_RETRIES_RAW,
        },
        reveal_secret=True,
    )
    provider = str(llm_provider if llm_provider is not None else resolved["LLM_PROVIDER"]["value"] or "openai_compatible").strip()
    api_key = str(llm_api_key if llm_api_key is not None else resolved["LLM_API_KEY"]["value"] or "").strip()
    base_url = str(llm_base_url if llm_base_url is not None else resolved["LLM_BASE_URL"]["value"] or "").strip()
    model = str(llm_model if llm_model is not None else resolved["LLM_MODEL"]["value"] or "").strip()
    timeout_raw = str(llm_timeout_seconds_raw if llm_timeout_seconds_raw is not None else resolved["LLM_TIMEOUT_SECONDS"]["value"] or "15").strip() or "15"
    retries_raw = str(llm_max_retries_raw if llm_max_retries_raw is not None else resolved["LLM_MAX_RETRIES"]["value"] or "1").strip() or "1"
    sources = {key: ("argument" if value is not None else resolved[key]["source"]) for key, value in {
        "LLM_PROVIDER": llm_provider,
        "LLM_BASE_URL": llm_base_url,
        "LLM_MODEL": llm_model,
        "LLM_API_KEY": llm_api_key,
        "LLM_TIMEOUT_SECONDS": llm_timeout_seconds_raw,
        "LLM_MAX_RETRIES": llm_max_retries_raw,
    }.items()}

    if requested_engine_type not in SUPPORTED_CONTENT_ENGINE_TYPES:
        return LLMConfigStatus(
            requested_engine_type=requested_engine_type,
            resolved_engine_type="rule_based",
            llm_provider=provider,
            llm_config_ready=False,
            status_code="unknown_content_engine",
            llm_base_url_status="configured" if base_url else "missing",
            llm_model_status="configured" if model else "missing",
            llm_api_key_status="configured" if api_key else "missing",
            llm_api_key_preview=_mask_api_key(api_key),
            timeout_seconds=LLM_TIMEOUT_SECONDS,
            max_retries=LLM_MAX_RETRIES,
            llm_provider_source=sources["LLM_PROVIDER"], llm_base_url_source=sources["LLM_BASE_URL"],
            llm_model_source=sources["LLM_MODEL"], llm_api_key_source=sources["LLM_API_KEY"],
            llm_timeout_seconds_source=sources["LLM_TIMEOUT_SECONDS"], llm_max_retries_source=sources["LLM_MAX_RETRIES"],
        )

    if requested_engine_type != "llm_openai_compatible":
        return LLMConfigStatus(
            requested_engine_type=requested_engine_type,
            resolved_engine_type=requested_engine_type,
            llm_provider=provider,
            llm_config_ready=False,
            status_code="llm_disabled",
            llm_base_url_status="configured" if base_url else "missing",
            llm_model_status="configured" if model else "missing",
            llm_api_key_status="configured" if api_key else "missing",
            llm_api_key_preview=_mask_api_key(api_key),
            timeout_seconds=LLM_TIMEOUT_SECONDS,
            max_retries=LLM_MAX_RETRIES,
            llm_provider_source=sources["LLM_PROVIDER"], llm_base_url_source=sources["LLM_BASE_URL"],
            llm_model_source=sources["LLM_MODEL"], llm_api_key_source=sources["LLM_API_KEY"],
            llm_timeout_seconds_source=sources["LLM_TIMEOUT_SECONDS"], llm_max_retries_source=sources["LLM_MAX_RETRIES"],
        )

    timeout_seconds, timeout_valid = _safe_float(timeout_raw, 15.0)
    max_retries, retries_valid = _safe_int(retries_raw, 1)
    base_url_resolved = _resolve_base_url(base_url)

    missing_fields: list[str] = []
    invalid_fields: list[str] = []

    if provider != "openai_compatible":
        invalid_fields.append("LLM_PROVIDER")
    if not api_key:
        missing_fields.append("LLM_API_KEY")
    if not base_url:
        missing_fields.append("LLM_BASE_URL")
    elif not base_url_resolved:
        invalid_fields.append("LLM_BASE_URL")
    if not model:
        missing_fields.append("LLM_MODEL")
    if not timeout_valid or timeout_seconds <= 0:
        invalid_fields.append("LLM_TIMEOUT_SECONDS")
    if not retries_valid or max_retries < 0:
        invalid_fields.append("LLM_MAX_RETRIES")

    if missing_fields or invalid_fields:
        return LLMConfigStatus(
            requested_engine_type=requested_engine_type,
            resolved_engine_type="rule_based",
            llm_provider=provider,
            llm_config_ready=False,
            status_code="llm_config_missing",
            missing_fields=tuple(missing_fields),
            invalid_fields=tuple(invalid_fields),
            llm_base_url_status="configured" if base_url else "missing",
            llm_model_status="configured" if model else "missing",
            llm_api_key_status="configured" if api_key else "missing",
            llm_api_key_preview=_mask_api_key(api_key),
            timeout_seconds=timeout_seconds,
            max_retries=max(0, max_retries),
            llm_provider_source=sources["LLM_PROVIDER"], llm_base_url_source=sources["LLM_BASE_URL"],
            llm_model_source=sources["LLM_MODEL"], llm_api_key_source=sources["LLM_API_KEY"],
            llm_timeout_seconds_source=sources["LLM_TIMEOUT_SECONDS"], llm_max_retries_source=sources["LLM_MAX_RETRIES"],
        )

    return LLMConfigStatus(
        requested_engine_type=requested_engine_type,
        resolved_engine_type="llm_openai_compatible",
        llm_provider=provider,
        llm_config_ready=True,
        status_code="llm_config_ready",
        llm_base_url_status="configured",
        llm_model_status="configured",
        llm_api_key_status="configured",
        llm_api_key_preview=_mask_api_key(api_key),
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        llm_provider_source=sources["LLM_PROVIDER"], llm_base_url_source=sources["LLM_BASE_URL"],
        llm_model_source=sources["LLM_MODEL"], llm_api_key_source=sources["LLM_API_KEY"],
        llm_timeout_seconds_source=sources["LLM_TIMEOUT_SECONDS"], llm_max_retries_source=sources["LLM_MAX_RETRIES"],
    )


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
    return _unique_texts(normalized, limit=MAX_HASHTAGS)


def _normalize_comments(values: Any) -> list[str]:
    if isinstance(values, str):
        candidates = [values]
    elif isinstance(values, list):
        candidates = [_strip_text(item) for item in values]
    else:
        candidates = []
    return _unique_texts([_truncate(item, MAX_COMMENT_LENGTH) for item in candidates], limit=4)


def _normalize_titles(values: Any) -> list[str]:
    if isinstance(values, str):
        candidates = [values]
    elif isinstance(values, list):
        candidates = [_strip_text(item) for item in values]
    else:
        candidates = []
    return _unique_texts([_truncate(item, MAX_TITLE_LENGTH) for item in candidates], limit=MAX_TITLES)


def _normalize_selling_points(values: Any) -> list[str]:
    candidates: list[str] = []
    if isinstance(values, list):
        for item in values:
            if isinstance(item, dict):
                title = _truncate(item.get("title"), 8)
                description = _truncate(item.get("description"), MAX_SELLING_POINT_LENGTH)
                if title and description:
                    candidates.append(f"{title} {description}")
                elif title or description:
                    candidates.append(title or description)
            else:
                candidates.append(_truncate(item, MAX_SELLING_POINT_LENGTH))
    elif isinstance(values, str):
        candidates = [_truncate(values, MAX_SELLING_POINT_LENGTH)]
    return _unique_texts(candidates, limit=REQUIRED_SELLING_POINTS)


def _strip_code_fence(content: str) -> str:
    cleaned = content.strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        lines = cleaned.splitlines()
        lines = [line for line in lines if not line.strip().startswith("```")]
        return "\n".join(lines).strip()
    return cleaned


def _extract_first_json_object(content: str) -> str | None:
    start = content.find("{")
    if start < 0:
        return None

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(content)):
        char = content[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return content[start : index + 1]
    return None


def _parse_llm_json_payload(content: str) -> dict[str, Any] | None:
    candidates = [content.strip()]
    stripped = _strip_code_fence(content)
    if stripped not in candidates:
        candidates.append(stripped)

    extracted = _extract_first_json_object(stripped)
    if extracted and extracted not in candidates:
        candidates.append(extracted)

    extracted_from_raw = _extract_first_json_object(content)
    if extracted_from_raw and extracted_from_raw not in candidates:
        candidates.append(extracted_from_raw)

    for candidate in candidates:
        if not candidate:
            continue
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return None


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
    title_patterns = copy_config.get("title_patterns", []) if isinstance(copy_config, dict) else []
    selling_points = copy_config.get("selling_points", []) if isinstance(copy_config, dict) else []
    hashtags = copy_config.get("hashtags", []) if isinstance(copy_config, dict) else []
    banned_word_hints = {
        "food": "避免出现护肤、收纳、清洁、功能产品、小物、随手用。",
        "beauty": "避免出现早餐、下午茶、收纳、厨房、浴室。",
        "home": "避免出现减肥、护肤功效、早餐口感等错类目表达。",
        "pet": "避免出现上妆、早餐、护肤等错类目表达。",
    }
    user_prompt = f"""
你要为小红书商品分享生成中文 JSON 文案。
只返回一个 JSON 对象。
不要返回 Markdown。
不要使用 ```json 代码块。
不要解释，不要补充多余文本，不要在 JSON 前后加说明。
字段必须完整，必须可被 json.loads 直接解析。

商品名称：{content_input.product_name or "未填写"}
用户类目：{content_input.category}
主类目：{main_category or "other"}
细分类目：{sub_category or "general"}
类目标签：{category_label}
商品描述：{content_input.description or "未填写"}
内容类型：{content_input.content_type}
风格：{content_input.style}
匹配关键词：{", ".join(matched_keywords) or "无"}
语气标签：{", ".join(tone_tags) or "无"}
参考标题方向：{", ".join(title_patterns[:3]) or "无"}
参考卖点方向：{", ".join(selling_points[:5]) or "无"}
参考标签方向：{", ".join(hashtags[:6]) or "无"}

内容要求：
1. 语气要像真实分享，不要像广告，不要像系统提示。
2. 不要写“可直接复制发布”“可编辑后发布”“发布说明”等系统文案。
3. 不要写医疗、减肥、保证效果、全网第一、最强、神器等表达。
4. 文案必须贴合细分类目，{banned_word_hints.get(main_category, "避免错类目串词。")}
5. 标题、正文、标签、评论引导、卖点都要和商品细分类目一致。
6. 正文更像小红书真实体验，不要空泛堆词。

输出 JSON schema：
{{
  "titles": ["标题1", "标题2", "标题3", "标题4", "标题5"],
  "body": "80到180字左右的中文正文",
  "hashtags": ["标签1", "标签2", "标签3", "标签4", "标签5"],
  "comment_prompts": ["评论引导1", "评论引导2", "评论引导3"],
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

长度约束：
- titles: 3 到 5 条，每条尽量不超过 24 个中文字符
- hashtags: 5 到 8 个短标签
- comment_prompts: 2 到 4 条
- selling_points: 固定 3 条
- selling_points.title: 尽量 4 到 8 个字
- selling_points.description: 尽量 8 到 18 个字
- body: 尽量 80 到 180 个中文字符
""".strip()
    return [
        {
            "role": "system",
            "content": (
                "你是中文小红书种草文案助手。"
                "你只能输出一个可直接解析的 JSON 对象。"
                "不要输出 markdown，不要输出解释。"
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

    if len(titles) < MIN_TITLES or not body:
        return None
    if len(selling_points) < REQUIRED_SELLING_POINTS:
        return None
    if any(copy in body for copy in SYSTEM_COPY_FORBIDDEN):
        return None

    note_data = dict(fallback_note_data)
    note_data["note_titles"] = titles
    note_data["note_body"] = body
    note_data["hashtags"] = hashtags or list(fallback_note_data.get("hashtags", []))[:MAX_HASHTAGS]
    note_data["comments"] = comments or list(fallback_note_data.get("comments", []))[:4]
    note_data["selling_points"] = selling_points[:REQUIRED_SELLING_POINTS]

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
    config_status = get_llm_config_status(content_engine_type="llm_openai_compatible")
    if not config_status.llm_config_ready:
        return LLMContentResult(success=False, error_message=config_status.status_code)

    resolved = get_runtime_config_values(
        ["LLM_MODEL", "LLM_API_KEY", "LLM_BASE_URL"],
        defaults={"LLM_MODEL": LLM_MODEL, "LLM_API_KEY": LLM_API_KEY, "LLM_BASE_URL": LLM_BASE_URL},
        reveal_secret=True,
    )
    model = str(resolved["LLM_MODEL"]["value"] or "")
    api_key = str(resolved["LLM_API_KEY"]["value"] or "")
    base_url = str(resolved["LLM_BASE_URL"]["value"] or "")
    request_payload = {
        "model": model,
        "messages": _build_messages(content_input),
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_error = "llm_request_failed"
    endpoint = _resolve_base_url(base_url)
    for _ in range(config_status.max_retries + 1):
        try:
            response_payload = _post_chat_completion(
                endpoint=endpoint,
                payload=request_payload,
                headers=headers,
                timeout_seconds=config_status.timeout_seconds,
            )
            content = _extract_message_content(response_payload)
            if not content:
                last_error = "llm_invalid_json"
                continue
            raw_data = _parse_llm_json_payload(content)
            if raw_data is None:
                last_error = "llm_invalid_json"
                continue
            note_data = _normalize_note_data(raw_data, fallback_note_data)
            if not note_data:
                last_error = "llm_schema_invalid"
                continue
            return LLMContentResult(success=True, note_data=note_data)
        except TimeoutError:
            last_error = "llm_timeout"
        except (error.URLError, OSError, json.JSONDecodeError, ValueError, TypeError):
            last_error = "llm_request_failed"
        except Exception:  # pragma: no cover
            last_error = "llm_request_failed"

    return LLMContentResult(success=False, error_message=last_error)
