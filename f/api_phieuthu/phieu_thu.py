from typing import Dict, Any, Optional

from f.api_phieuthu.main import run_base_extraction

DEFAULT_PROMPT_PATH = "f/information_extraction/prompt_phieu_thu"
DOC_TYPE = "phieu_thu"


def process_phieu_thu(
    file_content: bytes,
    model_path: Optional[str] = None,
    prompt_path: Optional[str] = None,
) -> Dict[str, Any]:
    return run_base_extraction(
        file_content=file_content,
        doc_type=DOC_TYPE,
        model_path=model_path,
        prompt_path=prompt_path or DEFAULT_PROMPT_PATH,
    )


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
