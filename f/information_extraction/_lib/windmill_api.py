import os
import re
import json
from typing import Any, Optional, Dict, Union
import httpx

PLATFORM_FOLDER = "platform"


class WindmillAPIError(Exception):
    pass


class WindmillPermissionError(WindmillAPIError):
    pass


class WindmillNotFoundError(WindmillAPIError):
    pass


def parse_str_input(val: Any, default: str = "") -> str:
    if val is None:
        return default
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, (int, float, bool)):
        return str(val).strip()
    if isinstance(val, dict):
        for key in ["path", "name", "value", "label", "id", "slug", "content", "tier", "model", "prompt"]:
            if key in val and val[key] is not None:
                extracted = parse_str_input(val[key], default="")
                if extracted:
                    return extracted
        for v in val.values():
            extracted = parse_str_input(v, default="")
            if extracted:
                return extracted
        return default
    if isinstance(val, (list, tuple)):
        for item in val:
            extracted = parse_str_input(item, default="")
            if extracted:
                return extracted
        return default
    return str(val).strip()


def parse_plain_text_to_dict(
    val: Any,
    schema: Optional[Dict[str, Any]] = None,
    current_val: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    if val is None:
        return current_val or {}
    if isinstance(val, dict):
        return val
    str_val = parse_str_input(val)
    if not str_val:
        return current_val or {}

    if (str_val.startswith("{") and str_val.endswith("}")) or (str_val.startswith("[") and str_val.endswith("]")):
        try:
            parsed_json = json.loads(str_val)
            if isinstance(parsed_json, dict):
                return parsed_json
        except Exception:
            pass

    result_dict = {}
    lines = [line.strip() for line in str_val.splitlines() if line.strip()]
    parsed_pairs = False
    for line in lines:
        if ":" in line or "=" in line:
            delimiter = ":" if ":" in line else "="
            parts = line.split(delimiter, 1)
            k = parts[0].strip()
            v = parts[1].strip()
            if k:
                if v.isdigit():
                    result_dict[k] = int(v)
                else:
                    try:
                        result_dict[k] = float(v)
                    except ValueError:
                        result_dict[k] = v
                parsed_pairs = True
    if parsed_pairs and result_dict:
        if current_val and isinstance(current_val, dict):
            updated = dict(current_val)
            updated.update(result_dict)
            return updated
        return result_dict

    schema_obj = schema.get("schema", schema) if (schema and isinstance(schema, dict)) else {}
    properties = schema_obj.get("properties", {}) if isinstance(schema_obj, dict) else {}
    required = schema_obj.get("required", []) if isinstance(schema_obj, dict) else []

    target_key = None
    for priority_key in ["content", "api_key", "text", "prompt", "value", "name", "slug"]:
        if priority_key in properties or priority_key in required:
            target_key = priority_key
            break
    if not target_key and properties:
        keys = list(properties.keys())
        if len(keys) == 1:
            target_key = keys[0]
    if not target_key and current_val and isinstance(current_val, dict):
        keys = list(current_val.keys())
        if len(keys) == 1:
            target_key = keys[0]
    if not target_key:
        target_key = "content"

    if current_val and isinstance(current_val, dict):
        updated = dict(current_val)
        updated[target_key] = str_val
        return updated
    return {target_key: str_val}


def get_workspace() -> str:
    workspace = os.getenv("WM_WORKSPACE")
    if not workspace:
        raise WindmillAPIError(
            "Biến môi trường 'WM_WORKSPACE' không tồn tại trong môi trường Windmill."
        )
    return workspace.strip()


def get_token() -> str:
    token = os.getenv("WM_TOKEN")
    if not token:
        raise WindmillAPIError(
            "Biến môi trường 'WM_TOKEN' không tồn tại. Không được hard-code token."
        )
    return token.strip()


def get_base_url() -> str:
    base_url = os.getenv("BASE_INTERNAL_URL") or os.getenv("WM_BASE_URL")
    if not base_url:
        raise WindmillAPIError(
            "Biến môi trường 'BASE_INTERNAL_URL' hoặc 'WM_BASE_URL' không tồn tại."
        )
    return base_url.rstrip("/")


def get_client() -> httpx.Client:
    return httpx.Client(
        base_url=f"{get_base_url()}/api",
        headers={
            "Authorization": f"Bearer {get_token()}",
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )


def clean_name(value: Any, field_name: str) -> str:
    parsed = parse_str_input(value)
    if not parsed:
        raise ValueError(f"Trường '{field_name}' không được để trống")
    if parsed.startswith("f/"):
        parsed = parsed[2:]
    parsed = parsed.strip("/")
    if not parsed:
        raise ValueError(f"Trường '{field_name}' không được để trống")
    if len(parsed) > 100:
        raise ValueError(f"Trường '{field_name}' không được dài quá 100 ký tự")
    if "/" in parsed or "\\" in parsed:
        raise ValueError(f"Tên '{field_name}' ('{parsed}') không được chứa ký tự '/' hoặc '\\'")
    if not re.fullmatch(r"[A-Za-z0-9_\-.]+", parsed):
        raise ValueError(
            f"Trường '{field_name}' ('{parsed}') chỉ được chứa ký tự A-Z, a-z, 0-9, _, -, ."
        )
    return parsed


def clean_path(value: Any, field_name: str) -> str:
    parsed = parse_str_input(value)
    if not parsed:
        raise ValueError(f"Trường '{field_name}' không được để trống")
    if parsed.startswith("f/"):
        parsed = parsed[2:]
    parsed = parsed.replace("\\", "/").strip("/")
    if not parsed:
        raise ValueError(f"Trường '{field_name}' không được để trống")
    segments = parsed.split("/")
    for segment in segments:
        if segment == ".." or segment == ".":
            raise ValueError(f"Đường dẫn '{field_name}' không hợp lệ (chứa '..')")
        if not re.fullmatch(r"[A-Za-z0-9_\-.]+", segment):
            raise ValueError(
                f"Phần '{segment}' trong đường dẫn '{field_name}' chỉ được chứa A-Z, a-z, 0-9, _, -, ."
            )
    return "/".join(segments)


def validate_folder_name(folder_name: Any) -> str:
    return clean_path(folder_name, "folder_name")


def validate_resource_name(resource_name: Any) -> str:
    return clean_path(resource_name, "resource_name")


def resource_path(folder_name: Any, resource_name: Any) -> str:
    res_str = parse_str_input(resource_name)
    folder_str = parse_str_input(folder_name)
    if res_str.startswith("f/"):
        res_clean = clean_path(res_str, "resource_name")
        return f"f/{res_clean}"
    folder_clean = clean_path(folder_str, "folder_name") if folder_str else ""
    res_clean = clean_path(res_str, "resource_name")
    if folder_clean and (res_clean == folder_clean or res_clean.startswith(folder_clean + "/")):
        return f"f/{res_clean}"
    if folder_clean:
        return f"f/{folder_clean}/{res_clean}"
    return f"f/{res_clean}"


def folder_path(folder_name: Any) -> str:
    folder_str = validate_folder_name(folder_name)
    return f"f/{folder_str}"


def is_platform(folder_name: Any) -> bool:
    clean = parse_str_input(folder_name).lower()
    if clean.startswith("f/"):
        clean = clean[2:]
    clean = clean.split("/")[0]
    return clean == PLATFORM_FOLDER


def ensure_not_platform(folder_name: Any) -> None:
    if is_platform(folder_name):
        raise WindmillPermissionError(
            "Folder 'platform' là folder hệ thống. Không được thay đổi hoặc xóa tài nguyên trong folder này."
        )


def raise_for_response(response: httpx.Response) -> None:
    if response.status_code == 401:
        raise WindmillPermissionError("Unauthorized: Token không hợp lệ hoặc đã hết hạn.")
    if response.status_code == 403:
        raise WindmillPermissionError("Forbidden: Không có quyền thực hiện thao tác này.")
    if response.status_code == 404:
        raise WindmillNotFoundError(f"Không tìm thấy tài nguyên (404 Not Found): {response.url}")
    if response.status_code >= 400:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise WindmillAPIError(f"Windmill API error {response.status_code}: {detail}")


def api_get(endpoint: str, params: Optional[dict] = None) -> Any:
    with get_client() as client:
        response = client.get(endpoint, params=params)
    raise_for_response(response)
    try:
        return response.json()
    except Exception:
        return response.text


def api_post(endpoint: str, payload: Any) -> Any:
    with get_client() as client:
        response = client.post(endpoint, json=payload)
    raise_for_response(response)
    try:
        return response.json()
    except Exception:
        return response.text


def api_delete(endpoint: str) -> Any:
    with get_client() as client:
        response = client.delete(endpoint)
    raise_for_response(response)
    try:
        return response.json()
    except Exception:
        return response.text