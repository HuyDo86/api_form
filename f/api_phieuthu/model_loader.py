try:
    import wmill
except ImportError:
    wmill = None

from typing import Dict, Any, Optional

DEFAULT_MODEL_PATH = "f/api_phieuthu/qwen_vlm"

PROVIDER_DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "gemini": "https://generativelanguage.googleapis.com",
    "anthropic": "https://api.anthropic.com",
}


def _detect_provider(model_name: str, raw_provider: Optional[str] = None) -> str:
    if raw_provider and isinstance(raw_provider, str) and raw_provider.strip():
        provider = raw_provider.strip().lower()
        if provider in ("openai", "gemini", "anthropic"):
            return provider

    model_lower = model_name.lower()
    if model_lower.startswith("gemini"):
        return "gemini"
    if model_lower.startswith("claude"):
        return "anthropic"
    return "openai"


def get_model_config(model_path: Optional[str] = None) -> Dict[str, Any]:
    path_to_load = model_path or DEFAULT_MODEL_PATH

    if not isinstance(path_to_load, str) or not path_to_load.startswith("f/"):
        raise ValueError(f"model_path không hợp lệ: {path_to_load}")

    if wmill is None:
        raise RuntimeError("Thư viện 'wmill' chưa được cài đặt trong môi trường hiện tại")

    try:
        model_cfg = wmill.get_resource(path_to_load)
    except Exception as exc:
        raise RuntimeError(
            f"Không load được model resource '{path_to_load}': {exc}"
        ) from exc

    if not isinstance(model_cfg, dict):
        raise ValueError(f"Model resource '{path_to_load}' không phải object")

    required_fields = ("model", "api_key")
    missing_fields = [field for field in required_fields if not model_cfg.get(field)]
    if missing_fields:
        raise ValueError(
            f"Model resource '{path_to_load}' thiếu field: {', '.join(missing_fields)}"
        )

    model_name = str(model_cfg["model"]).strip()
    provider = _detect_provider(model_name, model_cfg.get("provider"))
    default_base_url = PROVIDER_DEFAULT_BASE_URLS.get(provider, "https://api.openai.com/v1")
    base_url = str(model_cfg.get("base_url") or default_base_url).strip()

    temperature = 0.0
    if "temperature" in model_cfg and model_cfg["temperature"] is not None:
        try:
            temperature = float(model_cfg["temperature"])
        except (ValueError, TypeError):
            temperature = 0.0

    config = {
        "provider": provider,
        "model": model_name,
        "api_key": str(model_cfg["api_key"]).strip(),
        "base_url": base_url,
        "temperature": temperature,
    }

    if provider == "openai":
        if model_cfg.get("organization"):
            config["organization"] = str(model_cfg["organization"]).strip()
    elif provider == "gemini":
        config["api_version"] = str(model_cfg.get("api_version") or "v1beta").strip()
    elif provider == "anthropic":
        config["anthropic_version"] = str(model_cfg.get("anthropic_version") or "2023-06-01").strip()

    return config
