from __future__ import annotations

from typing import Any

SUPPORTED_LLM_YAML_KEYS = {
    "LLM_PROVIDER",
    "LLM_BASE_URL",
    "LLM_MODEL",
    "LLM_CHAT_COMPLETIONS_PATH",
    "LLM_API_KEY_REF",
}


def parse_llm_yaml(content: str | None) -> dict[str, str]:
    """Parse the deliberately small key=value subset used by llm.yaml."""
    settings: dict[str, str] = {}
    for raw_line in str(content or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key in SUPPORTED_LLM_YAML_KEYS and key != "LLM_API_KEY":
            settings[key] = value
    return settings


def extract_llm_yaml(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"llm_yaml_found": False, "content": "", "settings": {}}

    candidates: list[Any] = [payload.get("llm.yaml")]
    for container_key in ("files", "configs", "yamlFiles"):
        container = payload.get(container_key)
        if isinstance(container, dict):
            candidates.append(container.get("llm.yaml"))

    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return {
                "llm_yaml_found": True,
                "content": candidate,
                "settings": parse_llm_yaml(candidate),
            }
    return {"llm_yaml_found": False, "content": "", "settings": {}}
