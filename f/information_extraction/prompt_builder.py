import wmill
import textwrap
from typing import Optional, Dict, Any

DEFAULT_PROMPT_PATH = "f/information_extraction/prompt_phieu_thu"


def load_prompt_resource_dynamically(prompt_path: Optional[str] = None) -> Dict[str, Any]:
    path_to_load = prompt_path or DEFAULT_PROMPT_PATH
    try:
        resource = wmill.get_resource(path_to_load)
        if isinstance(resource, dict):
            return resource
        return {"content": str(resource)}
    except Exception as e:
        print(f"Warning: Không thể nạp prompt resource tại '{path_to_load}':", e)
        return {}


def format_prompt_dict_to_string(prompt_dict: Dict[str, Any], ocr_text: Optional[str] = None) -> str:
    if "content" in prompt_dict and isinstance(prompt_dict["content"], str) and prompt_dict["content"].strip():
        base_prompt = prompt_dict["content"].strip()
    else:
        role = prompt_dict.get("role", "")
        goal = prompt_dict.get("goal", "")
        instruction = prompt_dict.get("instruction", "")
        context = prompt_dict.get("context", "")
        constraints = prompt_dict.get("constraints", "")
        output = prompt_dict.get("output", "")

        parts = []
        if role:
            parts.append(f"# Role\n{role}")
        if goal:
            parts.append(f"# Goal\n{goal}")
        if instruction:
            parts.append(f"# Instructions\n{instruction}")
        if context:
            parts.append(f"# Context\n{context}")
        if constraints:
            parts.append(f"# Constraints\n{constraints}")
        if output:
            parts.append(f"# Output\n{output}")

        base_prompt = "\n\n".join(parts).strip()

    if ocr_text and ocr_text.strip():
        return f"{base_prompt}\n\n---------------------\nDỮ LIỆU OCR:\n{ocr_text.strip()}"

    return base_prompt


def build_prompt(
    ocr_text: Optional[str] = None,
    prompt_path: Optional[str] = None,
) -> str:
    prompt_dict = load_prompt_resource_dynamically(prompt_path)
    return format_prompt_dict_to_string(prompt_dict, ocr_text=ocr_text)