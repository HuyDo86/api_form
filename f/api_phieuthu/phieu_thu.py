# requirements:
# openai
# wmill

from typing import Dict, Any, Optional
import re

try:
    from f.api_phieuthu.main import (
        step_build_prompt,
        step_load_model,
        step_extract,
        step_parse_and_clean,
    )
except ModuleNotFoundError:
    try:
        from f.api_phieuthu.main import (
            step_build_prompt,
            step_load_model,
            step_extract,
            step_parse_and_clean,
        )
    except ModuleNotFoundError:
        from f.api_phieuthu.main import (
            step_build_prompt,
            step_load_model,
            step_extract,
            step_parse_and_clean,
        )

DEFAULT_PROMPT_PATH = "f/information_extraction/prompt_phieu_thu"
DOC_TYPE = "phieu_thu"


def _process_phieu_thu_fields(data: Dict[str, Any], ocr_text: str = "") -> Dict[str, Any]:
    if not isinstance(data, dict):
        return data

    text_lower = ocr_text.lower() if ocr_text else ""
    ref_docs = []
    hd_matches = re.findall(r"(?:hóa đơn gtgt|hóa đơn|hđgtgt|hd số|số hd)[:\s]*([a-zA-Z0-9/-]{3,20})", text_lower)
    for match in hd_matches:
        code = match.strip().upper()
        if code and len(code) >= 3 and not code.startswith("GTGT"):
            ref = f"Hóa đơn GTGT số {code}"
            if ref not in ref_docs:
                ref_docs.append(ref)
    hdong_matches = re.findall(r"(?:hợp đồng|hđ số|hđồng)[:\s]*([a-zA-Z0-9/-]{3,20})", text_lower)
    for match in hdong_matches:
        code = match.strip().upper()
        if code and len(code) >= 3:
            ref = f"Hợp đồng số {code}"
            if ref not in ref_docs:
                ref_docs.append(ref)
    if ref_docs and not data.get("other accounting documents"):
        data["other accounting documents"] = " | ".join(ref_docs)
    if not data.get("attach") and ref_docs:
        data["attach"] = f"Kèm theo {len(ref_docs)} chứng từ ({', '.join(ref_docs)})"
    if not data.get("Tax identification number"):
        mst_matches = re.findall(r"(?:mã số thuế|mst|tax code)[:\s]*([0-9]{10}(?:-[0-9]{3})?)", text_lower)
        if mst_matches:
            data["Tax identification number"] = mst_matches[0].upper()
    if data.get("total_amount/ grand_total") and not data.get("unit of measurement"):
        if "usd" in text_lower:
            data["unit of measurement"] = "USD"
        elif "eur" in text_lower:
            data["unit of measurement"] = "EUR"
        else:
            data["unit of measurement"] = "VND"
    if not data.get("sign") or not isinstance(data.get("sign"), list):
        signs_found = []
        sign_keywords = ["giám đốc", "kế toán trưởng", "người nộp tiền", "người lập phiếu", "thủ quỹ"]
        for kw in sign_keywords:
            if kw in text_lower:
                signs_found.append(kw.title())
        if signs_found:
            data["sign"] = signs_found

    return {k: v for k, v in data.items() if v is not None}


def process_phieu_thu(
    file_content: Any,
    model_path: Optional[str] = None,
    prompt_path: Optional[str] = None,
) -> Dict[str, Any]:
    actual_prompt_path = prompt_path or DEFAULT_PROMPT_PATH
    prompt = step_build_prompt(actual_prompt_path)
    model_cfg = step_load_model(model_path)
    raw_output = step_extract(model_cfg, prompt, image_input=file_content)
    data = step_parse_and_clean(raw_output)
    data = _process_phieu_thu_fields(data, raw_output)
    return {
        "document_type": DOC_TYPE,
        "extracted_data": data,
    }


def main(
    file_content: Any,
    model_path: Optional[str] = None,
    prompt_path: Optional[str] = None,
) -> Dict[str, Any]:
    return process_phieu_thu(
        file_content=file_content,
        model_path=model_path,
        prompt_path=prompt_path,
    )

