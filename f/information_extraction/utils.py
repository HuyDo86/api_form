import os
import json
import re
from typing import Union, Any
import base64


def _normalize_text_value(value: Any) -> str:
    if not isinstance(value, str):
        return ""

    text = value.strip()
    if not text:
        return ""

    MAX_DEPTH = 10

    for _ in range(MAX_DEPTH):
        prev_text = text

        try:
            payload = json.loads(text)
            if isinstance(payload, dict):
                for key in [
                    "markdown_text",
                    "ocr_input_text",
                    "text",
                    "content",
                    "raw_output",
                ]:
                    if key in payload and isinstance(payload[key], str):
                        text = payload[key].strip()
                        break
        except Exception:
            pass

        try:

            missing_padding = len(text) % 4
            if missing_padding:
                text_padded = text + "=" * (4 - missing_padding)
            else:
                text_padded = text

            decoded_bytes = base64.b64decode(text_padded)
            decoded_text = decoded_bytes.decode("utf-8", errors="ignore").strip()

            if decoded_text and any(c.isalpha() for c in decoded_text):
                text = decoded_text
        except Exception:
            pass


        if text == prev_text:
            break

    return text


def parse_input_text(file_content: Union[bytes, str, dict]) -> str:
    if file_content is None:
        return ""
    if isinstance(file_content, bytes):
        for encoding in ["utf-8-sig", "utf-8", "utf-16", "latin-1"]:
            try:
                text = file_content.decode(encoding)
                break
            except Exception:
                continue
        else:
            text = file_content.decode("utf-8", errors="ignore")
    elif isinstance(file_content, dict):
        for key in ["markdown_text", "ocr_input_text", "text", "content", "raw_output"]:
            if key in file_content and isinstance(file_content[key], str):
                return _normalize_text_value(file_content[key])
        return _normalize_text_value(json.dumps(file_content, ensure_ascii=False))
    else:
        text = str(file_content)

    text = text.strip()
    if os.path.exists(text) and os.path.isfile(text):
        try:
            with open(text, "r", encoding="utf-8", errors="ignore") as f:
                file_str = f.read().strip()
                if file_str:
                    text = file_str
        except Exception:
            pass
    return _normalize_text_value(text)


def extract_json(raw_text: str) -> dict:
    cleaned = re.sub(r"```json\s*|\s*```", "", raw_text).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    return json.loads(cleaned)


def clean_extracted_data(data: Any) -> Any:
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            if v is None:
                continue
            if isinstance(v, (dict, list)):
                cv = clean_extracted_data(v)
                if cv or cv == 0 or cv is False:
                    cleaned[k] = cv
            else:
                cleaned[k] = v
        return cleaned
    elif isinstance(data, list):
        cleaned_list = []
        for item in data:
            if item is None:
                continue
            if isinstance(item, (dict, list)):
                ci = clean_extracted_data(item)
                if ci or ci == 0 or ci is False:
                    cleaned_list.append(ci)
            else:
                cleaned_list.append(item)
        return cleaned_list
    return data


def compute_accuracy_score(ocr_text: str, extracted_data: Any) -> float:
    if not isinstance(ocr_text, str) or not ocr_text.strip():
        return 0.0

    ocr_norm = re.sub(r"\s+", " ", ocr_text).strip().lower()
    if not ocr_norm:
        return 0.0

    def walk(value: Any) -> tuple[int, int]:
        matched = 0
        total = 0
        if isinstance(value, dict):
            for key, item in value.items():
                if isinstance(item, (dict, list)):
                    sub_matched, sub_total = walk(item)
                    matched += sub_matched
                    total += sub_total
                elif item is not None and str(item).strip():
                    total += 1
                    key_text = str(key).lower()
                    item_text = str(item).lower()
                    if key_text in ocr_norm or item_text in ocr_norm:
                        matched += 1
        elif isinstance(value, list):
            for item in value:
                sub_matched, sub_total = walk(item)
                matched += sub_matched
                total += sub_total
        return matched, total

    matched, total = walk(extracted_data)
    if total == 0:
        return 0.0
    return round((matched / total) * 100.0, 2)
