from typing import Dict, Any, Optional

from f.information_extraction.main import (
    step_load_model,
    step_build_prompt,
    step_extract,
    step_parse_and_clean,
)

DEFAULT_PROMPT_PATH = "f/information_extraction/prompt_phieu_thu"
DOC_TYPE = "phieu_thu"


def process_phieu_thu(
    file_content: Any,
    model_path: Optional[str] = None,
    prompt_path: Optional[str] = None,
) -> Dict[str, Any]:
    actual_prompt_path = prompt_path or DEFAULT_PROMPT_PATH
    model_cfg = step_load_model(model_path)
    prompt = step_build_prompt(ocr_text=None, prompt_path=actual_prompt_path)
    raw_output = step_extract(model_cfg, prompt, image_input=file_content)
    data = step_parse_and_clean(raw_output)
    return {
        "document_type": DOC_TYPE,
        "extracted_data": data,
    }


def main(
    file_content: bytes,
    model_path: Optional[str] = None,
    prompt_path: Optional[str] = None,
) -> Dict[str, Any]:
    return process_phieu_thu(
        file_content=file_content,
        model_path=model_path,
        prompt_path=prompt_path,
    )