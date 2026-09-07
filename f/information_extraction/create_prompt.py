import os
import yaml
from typing import Dict, Any, Optional
import wmill
from f.information_extraction._lib.windmill_api import (
    validate_folder_name,
    validate_resource_name,
    resource_path,
    ensure_not_platform,
    parse_str_input,
)

DEFAULT_PROMPT_PATH = "f/information_extraction/prompt_phieu_thu"

SCHEMA_KEYS = {
    "role": "Role",
    "goal": "Goal",
    "instruction": "Instruction",
    "context": "Context",
    "constraints": "Constraints",
    "output": "Output",
}

READ_ALIASES = {
    "role": ["Role", "role"],
    "goal": ["Goal", "goal"],
    "instruction": ["Instruction", "Instructions", "instruction", "instructions"],
    "context": ["Context", "context"],
    "constraints": ["Constraints", "constraint", "constraints"],
    "output": ["Output", "output"],
}

def get_default_prompt_fields() -> Dict[str, Optional[str]]:

    raw = wmill.get_resource(DEFAULT_PROMPT_PATH)

    print("RAW DEFAULT RESOURCE:", raw)  # DEBUG quan trọng

    if not isinstance(raw, dict):
        raise ValueError(f"Default resource must be dict, got: {type(raw)}")
    data = raw.get("value", raw)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid resource structure: {data}")

    result: Dict[str, Optional[str]] = {}
    for field, aliases in READ_ALIASES.items():
        val = None
        for alias in aliases:
            if alias in data:
                val = data[alias]
                break
        if val is None:
            lowered = {str(k).strip().lower(): v for k, v in data.items()}
            val = lowered.get(field)
        result[field] = parse_str_input(val)

    print("DEFAULTS PARSED:", result)
    return result

def resolve_field(
    input_value: Optional[str],
    default_value: Optional[str],
    field_name: str
) -> str:

    parsed_input = parse_str_input(input_value)

    if parsed_input:
        return parsed_input

    if default_value:
        return default_value

    raise ValueError(
        f"Field '{field_name}' không có giá trị (input + default đều rỗng)"
    )

def main(
    folder_name: str,
    prompt_name: str,
    role: Optional[str] = None,
    goal: Optional[str] = None,
    instruction: Optional[str] = None,
    context: Optional[str] = None,
    constraints: Optional[str] = None,
    output: Optional[str] = None,
    save_to_file: bool = False,
) -> Dict[str, Any]:

    clean_folder = validate_folder_name(folder_name)
    clean_prompt_name = validate_resource_name(prompt_name)
    ensure_not_platform(clean_folder)
    defaults = get_default_prompt_fields()
    value = {
        "role": resolve_field(role, defaults.get("role"), "role"),
        "goal": resolve_field(goal, defaults.get("goal"), "goal"),
        "instruction": resolve_field(instruction, defaults.get("instruction"), "instruction"),
        "context": resolve_field(context, defaults.get("context"), "context"),
        "constraints": resolve_field(constraints, defaults.get("constraints"), "constraints"),
        "output": resolve_field(output, defaults.get("output"), "output"),
    }

    print("FINAL PROMPT VALUE (internal lowercase):", value)
    stored_value = {SCHEMA_KEYS[field]: val for field, val in value.items()}
    print("STORE VALUE (schema keys):", stored_value)
    path = resource_path(clean_folder, clean_prompt_name)

    wmill.set_resource(
        path=path,
        value=stored_value,
        resource_type="c_my_prompt"
    )
    if save_to_file:
        try:
            cwd = os.getcwd()
            f_dir = os.path.join(cwd, "f") if os.path.basename(cwd) != "f" else cwd

            if not os.path.exists(f_dir):
                parent_f = os.path.join(os.path.dirname(cwd), "f")
                if os.path.exists(parent_f):
                    f_dir = parent_f

            target_folder = os.path.join(f_dir, clean_folder)
            os.makedirs(target_folder, exist_ok=True)

            file_path = os.path.join(
                target_folder,
                f"{clean_prompt_name}.resource.yaml"
            )

            yaml_data = {
                "description": "",
                "value": stored_value,
                "resource_type": "c_my_prompt",
            }

            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(yaml_data, f, allow_unicode=True, sort_keys=False)

            print(f"Saved YAML resource at: {file_path}")

        except Exception as e:
            print(f"Warning: Git sync save failed: {e}")

    return {
        "status": "prompt_created",
        "path": path,
    }
