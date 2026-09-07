import wmill
from typing import Dict, Any


DEFAULT_MODEL_PATH = "f/information_extraction/qwen_vlm"


def get_model_config(model_path: str | None = None) -> Dict[str, Any]:

    if not model_path:
        model_path = DEFAULT_MODEL_PATH

    if not isinstance(model_path, str) or not model_path.startswith("f/"):
        raise ValueError(f"model_path không hợp lệ: {model_path}")

    try:
        model_cfg = wmill.get_resource(model_path)
    except Exception as e:
        raise Exception(f"Không load được model resource: {model_path} | {e}")

    if not isinstance(model_cfg, dict):
        raise Exception(f"Resource {model_path} không phải dict")

    if not model_cfg.get("base_url"):
        raise Exception(f"Model thiếu field 'base_url' tại {model_path}")

    if not model_cfg.get("api_key"):
        raise Exception(
            f"Model '{model_path}' chưa có api_key. "
            f"Vui lòng cập nhật api_key."
        )

    model_name = model_cfg.get("model") 

    return {
        "api_key": model_cfg.get("api_key"),
        "base_url": model_cfg.get("base_url"),
        "model": model_name,
    }