from app.services.llm_config_parser import extract_llm_yaml, parse_llm_yaml


def test_parse_llm_yaml_supports_safe_fields_without_plain_api_key():
    parsed = parse_llm_yaml(
        "LLM_PROVIDER=deepseek\nLLM_BASE_URL=https://example.com/v1\n"
        "LLM_MODEL=deepseek-chat\nLLM_CHAT_COMPLETIONS_PATH=/chat/completions\n"
        "LLM_API_KEY_REF=secret://zhongcaoji/test/key\nLLM_API_KEY=do-not-parse\n"
    )
    assert parsed == {
        "LLM_PROVIDER": "deepseek",
        "LLM_BASE_URL": "https://example.com/v1",
        "LLM_MODEL": "deepseek-chat",
        "LLM_CHAT_COMPLETIONS_PATH": "/chat/completions",
        "LLM_API_KEY_REF": "secret://zhongcaoji/test/key",
    }


def test_extract_llm_yaml_supports_all_response_shapes():
    content = "LLM_PROVIDER=deepseek\n"
    for payload in [
        {"llm.yaml": content},
        {"files": {"llm.yaml": content}},
        {"configs": {"llm.yaml": content}},
        {"yamlFiles": {"llm.yaml": content}},
    ]:
        result = extract_llm_yaml(payload)
        assert result["llm_yaml_found"] is True
        assert result["settings"]["LLM_PROVIDER"] == "deepseek"


def test_extract_llm_yaml_missing_is_safe():
    result = extract_llm_yaml({"files": {"other.yaml": "x=y"}})
    assert result == {"llm_yaml_found": False, "content": "", "settings": {}}
