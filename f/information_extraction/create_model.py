from typing import Dict, Any, Literal
import wmill
from f.information_extraction._lib.windmill_api import (
    validate_folder_name,
    validate_resource_name,
    resource_path,
    ensure_not_platform,
    parse_str_input,
)

RESOURCE_TYPE = "c_my_model"

PROVIDER_CONFIG: Dict[str, Dict[str, Any]] = {
    "openai": {
        "label": "OpenAI",
        "default_base_url": "https://api.openai.com/v1",
        "model_example": "gpt-4o, gpt-4o-mini, o3-mini...",
    },
    "anthropic": {
        "label": "Anthropic",
        "default_base_url": "https://api.anthropic.com",
        "model_example": "claude-sonnet-4-5, claude-opus-4-1, claude-3-5-haiku-latest...",
    },
    "google": {
        "label": "Google (Gemini)",
        "default_base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "model_example": "gemini-2.5-pro, gemini-2.5-flash, gemini-2.0-flash...",
    },
    "meta": {
        "label": "Meta (Llama)",
        "default_base_url": None,
        "model_example": "Llama-3.3-70B-Instruct, Llama-3.1-8B-Instruct...",
    },
    "alibaba": {
        "label": "Alibaba (Qwen)",
        "default_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model_example": "qwen-max, qwen-plus, qwen2.5-vl-72b-instruct...",
    },
}


def main(
    folder_name: str,
    model_name: str,
    provider: Literal["openai", "anthropic", "google", "meta", "alibaba"],
    model: str,
    api_key: str,
    base_url: str = "",
) -> Dict[str, Any]:
    clean_folder = validate_folder_name(folder_name)
    clean_model_name = validate_resource_name(model_name)
    ensure_not_platform(clean_folder)
    clean_provider = parse_str_input(provider).strip().lower()
    if clean_provider not in PROVIDER_CONFIG:
        allowed = ", ".join(PROVIDER_CONFIG.keys())
        raise Exception(
            f"Provider '{clean_provider}' không được hỗ trợ. "
            f"Chọn một trong: {allowed}."
        )
    provider_cfg = PROVIDER_CONFIG[clean_provider]

    str_model = parse_str_input(model)
    if not str_model:
        raise Exception(
            f"Trường 'model' là bắt buộc đối với provider '{clean_provider}'. "
            f"Ví dụ: {provider_cfg.get('model_example', '')}"
        )

    str_api_key = parse_str_input(api_key)
    if not str_api_key:
        raise Exception(
            f"Trường 'api_key' là bắt buộc đối với provider '{clean_provider}'."
        )
    str_base_url = parse_str_input(base_url)
    if not str_base_url:
        str_base_url = provider_cfg.get("default_base_url") or ""
    if not str_base_url:
        raise Exception(
            f"Provider '{clean_provider}' không có base_url mặc định. "
            "Bạn phải nhập 'base_url' (endpoint OpenAI-compatible của nền tảng/gateway đang dùng)."
        )
    if not (str_base_url.startswith("http://") or str_base_url.startswith("https://")):
        raise Exception(
            f"'base_url' không hợp lệ: '{str_base_url}'. Phải bắt đầu bằng http:// hoặc https://"
        )

    path = resource_path(clean_folder, clean_model_name)
    existing_resource = wmill.get_resource(path, none_if_undefined=True)
    if existing_resource is not None:
        raise Exception(
            f"Model/Resource đã tồn tại tại đường dẫn '{path}'. "
            "Vui lòng chọn 'model_name' khác."
        )

    value = {
        "provider": clean_provider,
        "model": str_model,
        "api_key": str_api_key,
        "base_url": str_base_url,
    }
    wmill.set_resource(
        value=value,
        path=path,
        resource_type=RESOURCE_TYPE,
    )

    return {
        "status": "model_created",
        "path": path,
    }
