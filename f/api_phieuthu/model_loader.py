import wmill
from typing import Dict, Any, Optional

DEFAULT_MODEL_PATH = "f/information_extraction/qwen"


def get_model_config(model_path: Optional[str] = None) -> Dict[str, Any]:
    path_to_load = model_path or DEFAULT_MODEL_PATH

    if not isinstance(path_to_load, str) or not path_to_load.startswith("f/"):
        raise ValueError(f"model_path không hợp lệ: {path_to_load}")

    try:
        model_cfg = wmill.get_resource(path_to_load)
    except Exception as exc:
        raise RuntimeError(
            f"Không load được model resource '{path_to_load}': {exc}"
        ) from exc

    if not isinstance(model_cfg, dict):
        raise ValueError(f"Model resource '{path_to_load}' không phải object")

    required_fields = ("model", "base_url", "api_key")
    missing_fields = [field for field in required_fields if not model_cfg.get(field)]
    if missing_fields:
        raise ValueError(
            f"Model resource '{path_to_load}' thiếu field: {', '.join(missing_fields)}"
        )

    return {
        "api_key": model_cfg["api_key"],
        "base_url": model_cfg["base_url"],
        "model": model_cfg["model"],
    }
