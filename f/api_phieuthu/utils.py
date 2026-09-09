import json
import re
from typing import Any


def extract_json(raw_text: str) -> dict:
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise ValueError("Model không trả về nội dung")

    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw_text).strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        start = cleaned.find("{")
        if start < 0:
            raise ValueError("Không tìm thấy JSON object trong kết quả model")
        data, _ = decoder.raw_decode(cleaned[start:])

    if not isinstance(data, dict):
        raise ValueError("Kết quả model phải là một JSON object")
    return data


def clean_extracted_data(data: Any, drop_null: bool = True) -> Any:
    """Recursively copy JSON data, omitting keys with None/null values if drop_null is True."""
    if isinstance(data, dict):
        res = {}
        for key, value in data.items():
            if drop_null and value is None:
                continue
            cleaned = clean_extracted_data(value, drop_null=drop_null)
            if drop_null and cleaned is None:
                continue
            res[key] = cleaned
        return res
    if isinstance(data, list):
        return [clean_extracted_data(item, drop_null=drop_null) for item in data]
    return data
