from typing import Dict, Any, Optional

from f.information_extraction.utils import extract_json, clean_extracted_data
from f.information_extraction.prompt_builder import build_prompt
from f.information_extraction.model_loader import get_model_config
from f.information_extraction.llm import call_llm


def step_build_prompt(prompt_path: Optional[str] = None) -> str:
    return build_prompt(prompt_path)


def step_load_model(model_path: Optional[str] = None) -> Dict[str, Any]:
    return get_model_config(model_path)


def step_extract(
    model_cfg: Dict[str, Any],
    prompt: str,
    image_input: Any,
) -> str:
    return call_llm(model_cfg, prompt, image_input=image_input)


def step_parse_and_clean(raw_output: str) -> Dict[str, Any]:
    return clean_extracted_data(extract_json(raw_output))


def run_base_extraction(
    file_content: bytes,
    doc_type: str,
    model_path: Optional[str] = None,
    prompt_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Extract structured data directly from an image with one VLM request."""
    model_cfg = step_load_model(model_path)
    prompt = step_build_prompt(prompt_path)
    raw_output = step_extract(model_cfg, prompt, image_input=file_content)
    data = step_parse_and_clean(raw_output)

    return {
        "document_type": doc_type,
        "extracted_data": data,
    }
