import wmill

from typing import Optional, Dict, Any

DEFAULT_PROMPT_PATH = "f/information_extraction/prompt_phieu_thu"
PROMPT_SECTIONS = (
    ("Role", "role"),
    ("Goal", "goal"),
    ("Instructions", "instruction"),
    ("Context", "context"),
    ("Constraints", "constraints"),
    ("Output", "output"),
)


def load_prompt_resource_dynamically(prompt_path: Optional[str] = None) -> Dict[str, Any]:
    path_to_load = prompt_path or DEFAULT_PROMPT_PATH
    try:
        resource = wmill.get_resource(path_to_load)
    except Exception as exc:
        raise RuntimeError(
            f"Không thể nạp prompt resource tại '{path_to_load}': {exc}"
        ) from exc

    if isinstance(resource, dict):
        return resource
    if isinstance(resource, str) and resource.strip():
        return {"content": resource}
    raise ValueError(f"Prompt resource '{path_to_load}' không có nội dung hợp lệ")


def _get_section(prompt_dict: Dict[str, Any], key: str) -> Any:
    return prompt_dict.get(key, prompt_dict.get(key.capitalize(), ""))


def format_prompt_dict_to_string(prompt_dict: Dict[str, Any]) -> str:
    content = prompt_dict.get("content", prompt_dict.get("Content"))
    if isinstance(content, str) and content.strip():
        return content.strip()

    parts = []
    for heading, key in PROMPT_SECTIONS:
        value = _get_section(prompt_dict, key)
        if value is not None and str(value).strip():
            parts.append(f"# {heading}\n{str(value).strip()}")

    prompt = "\n\n".join(parts).strip()
    if not prompt:
        raise ValueError("Prompt resource không chứa content hoặc các trường prompt hợp lệ")
    return prompt


def build_prompt(prompt_path: Optional[str] = None) -> str:
    prompt_dict = load_prompt_resource_dynamically(prompt_path)
    return format_prompt_dict_to_string(prompt_dict)
