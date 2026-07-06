from app.services import content_engine_adapter, llm_content_service
from app.services.content_engine_adapter import (
    ContentGenerateInput,
    generate_content,
    resolve_content_engine_type,
)
from app.services.note_builder import build_result_payload


class _FakeTimeout(TimeoutError):
    pass


def _sample_input(**overrides):
    payload = {
        "product_name": "保温杯",
        "category": "家居日用",
        "description": "通勤带着方便，放包里也省心",
        "content_type": "好物推荐",
        "style": "清新简约",
    }
    payload.update(overrides)
    return ContentGenerateInput(**payload)


def _enable_llm(monkeypatch):
    monkeypatch.setattr(content_engine_adapter, "CONTENT_ENGINE_TYPE", "llm_openai_compatible")
    monkeypatch.setattr(llm_content_service, "LLM_PROVIDER", "openai_compatible")
    monkeypatch.setattr(llm_content_service, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(llm_content_service, "LLM_BASE_URL", "https://example.com/v1")
    monkeypatch.setattr(llm_content_service, "LLM_MODEL", "demo-model")
    monkeypatch.setattr(llm_content_service, "LLM_MAX_RETRIES", 0)


def test_content_engine_type_defaults_to_rule_based(monkeypatch):
    monkeypatch.setattr(content_engine_adapter, "CONTENT_ENGINE_TYPE", "")

    assert resolve_content_engine_type() == "rule_based"


def test_rule_based_engine_generates_compatible_note_data(monkeypatch):
    monkeypatch.setattr(content_engine_adapter, "CONTENT_ENGINE_TYPE", "rule_based")

    result = generate_content(
        _sample_input(
            product_name="水牛奶蛋糕",
            category="食品饮品",
            description="适合早餐和下午茶",
        )
    )

    assert result.success is True
    assert result.engine_type == "rule_based"
    assert result.error_message is None
    assert result.note_data["cover_title"]
    assert result.note_data["note_body"]
    assert result.note_data["sub_category"] == "bakery"


def test_llm_placeholder_falls_back_to_rule_based(monkeypatch):
    monkeypatch.setattr(content_engine_adapter, "CONTENT_ENGINE_TYPE", "llm_placeholder")

    result = generate_content(
        _sample_input(
            product_name="护手霜",
            category="美妆护肤",
            description="放包里随身带，洗完手顺手涂一点",
            content_type="真实测评",
            style="温柔日常",
        )
    )

    assert result.success is True
    assert result.engine_type == "rule_based"
    assert result.note_data["sub_category"] == "hand_body_care"
    assert result.error_message is not None


def test_llm_openai_compatible_missing_key_falls_back(monkeypatch):
    monkeypatch.setattr(content_engine_adapter, "CONTENT_ENGINE_TYPE", "llm_openai_compatible")
    monkeypatch.setattr(llm_content_service, "LLM_PROVIDER", "openai_compatible")
    monkeypatch.setattr(llm_content_service, "LLM_API_KEY", "")
    monkeypatch.setattr(llm_content_service, "LLM_BASE_URL", "https://example.com/v1")
    monkeypatch.setattr(llm_content_service, "LLM_MODEL", "demo-model")

    result = generate_content(_sample_input())

    assert result.success is True
    assert result.engine_type == "rule_based"
    assert result.error_message is not None
    assert result.note_data["sub_category"] == "cup_bottle"


def test_llm_openai_compatible_uses_llm_note_data_when_valid(monkeypatch):
    _enable_llm(monkeypatch)

    long_title = "通勤保温杯真的值得放包里每天带着出门补水"
    long_body = "这只保温杯我最近通勤会一直带着，容量刚好，放包里也比较省心，车里和办公室切换着用都很顺手。" * 5

    def fake_post(*, endpoint, payload, headers, timeout_seconds):
        assert endpoint == "https://example.com/v1/chat/completions"
        assert payload["model"] == "demo-model"
        assert headers["Authorization"] == "Bearer test-key"
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"titles": ["%s", "日常补水更顺手"], "body": "%s", "hashtags": ["通勤带", "日常补水", "冷热饮"], "comment_prompts": ["你更在意容量还是保温？"], "selling_points": [{"title": "容量刚好", "description": "通勤不会太重"}, {"title": "日常补水", "description": "带着更方便"}, {"title": "冷热饮都行", "description": "办公室和外出都适合"}], "summary_title": "通勤补水更轻松", "suitable_for": "通勤上班族", "recommend_reason": "放包里也省心", "summary_sentence": "通勤和日常补水都适合。"}' % (long_title, long_body)
                    }
                }
            ]
        }

    monkeypatch.setattr(llm_content_service, "_post_chat_completion", fake_post)

    result = generate_content(_sample_input())

    assert result.success is True
    assert result.engine_type == "llm_openai_compatible"
    assert result.error_message is None
    assert result.note_data["sub_category"] == "cup_bottle"
    assert all(tag.startswith("#") for tag in result.note_data["hashtags"])
    assert len(result.note_data["note_titles"][0]) <= llm_content_service.MAX_TITLE_LENGTH
    assert len(result.note_data["note_body"]) <= llm_content_service.MAX_BODY_LENGTH
    assert result.note_data["selling_points"] == ["容量刚好 通勤不会太重", "日常补水 带着更方便", "冷热饮都行 办公室和外出都适合"]


def test_llm_openai_compatible_invalid_json_falls_back(monkeypatch):
    _enable_llm(monkeypatch)
    monkeypatch.setattr(
        llm_content_service,
        "_post_chat_completion",
        lambda **_: {"choices": [{"message": {"content": "not-json"}}]},
    )

    result = generate_content(_sample_input(product_name="水牛奶蛋糕", category="食品饮品", description="适合早餐和下午茶"))

    assert result.success is True
    assert result.engine_type == "rule_based"
    assert result.error_message is not None
    assert result.note_data["sub_category"] == "bakery"


def test_llm_openai_compatible_missing_fields_falls_back(monkeypatch):
    _enable_llm(monkeypatch)
    monkeypatch.setattr(
        llm_content_service,
        "_post_chat_completion",
        lambda **_: {"choices": [{"message": {"content": '{"titles": ["只有标题"], "body": "正文"}'}}]},
    )

    result = generate_content(_sample_input(product_name="护手霜", category="美妆护肤"))

    assert result.success is True
    assert result.engine_type == "rule_based"
    assert result.error_message is not None
    assert result.note_data["sub_category"] == "hand_body_care"


def test_llm_openai_compatible_timeout_falls_back(monkeypatch):
    _enable_llm(monkeypatch)

    def raise_timeout(**_):
        raise _FakeTimeout("timeout")

    monkeypatch.setattr(llm_content_service, "_post_chat_completion", raise_timeout)

    result = generate_content(_sample_input())

    assert result.success is True
    assert result.engine_type == "rule_based"
    assert "fallback" in (result.error_message or "")


def test_invalid_content_engine_type_falls_back_to_rule_based(monkeypatch):
    monkeypatch.setattr(content_engine_adapter, "CONTENT_ENGINE_TYPE", "mystery")

    result = generate_content(_sample_input())

    assert result.success is True
    assert result.engine_type == "rule_based"
    assert result.note_data["sub_category"] == "cup_bottle"


def test_note_builder_uses_content_engine_adapter_and_keeps_shape(monkeypatch):
    monkeypatch.setattr(content_engine_adapter, "CONTENT_ENGINE_TYPE", "llm_placeholder")

    payload = build_result_payload(
        description="办公室早八备着喝，搭早餐也自然",
        content_type="好物推荐",
        style="清新简约",
        image_paths=[],
        product_name="挂耳咖啡",
        category="其他好物",
    )

    assert payload["cover_title"]
    assert payload["cover_subtitle"]
    assert payload["selling_points"]
    assert payload["summary_title"]
    assert payload["note_titles"]
    assert payload["note_body"]
    assert payload["hashtags"]
    assert payload["comments"]
    assert payload["sub_category"] == "drink"
    assert payload["content_engine_warning"] is not None
