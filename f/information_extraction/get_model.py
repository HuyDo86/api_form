from typing import Dict, Any
import wmill
from f.information_extraction._lib.windmill_api import (
    validate_folder_name,
    validate_resource_name,
    resource_path,
    ensure_not_platform,
)


def main(
    folder_name: str,
    model_name: str
) -> Dict[str, Any]:

    clean_folder = validate_folder_name(folder_name)
    clean_model_name = validate_resource_name(model_name)
    ensure_not_platform(clean_folder)

    path = resource_path(clean_folder, clean_model_name)

    try:
        model_cfg = wmill.get_resource(path)
    except Exception:
        raise Exception(f"Không tìm thấy model: {path}")

    if not isinstance(model_cfg, dict):
        raise Exception("Resource model bị lỗi format")


    model_name = model_cfg.get("model")
    base_url = model_cfg.get("base_url")
    active = model_cfg.get("active", False)


    return {
        "path": path,
        "model": model_name,
        "base_url": base_url,
        "has_api_key": bool(model_cfg.get("api_key"))  # chỉ check, không trả key
    }