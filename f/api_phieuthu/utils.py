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


def clean_extracted_data(data: Any) -> Any:
    if isinstance(data, dict):
        return {key: clean_extracted_data(value) for key, value in data.items()}
    if isinstance(data, list):
        return [clean_extracted_data(item) for item in data]
    return data
