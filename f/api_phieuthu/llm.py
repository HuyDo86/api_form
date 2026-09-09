# requirements:
# openai

import base64
import os
from typing import Dict, Any

from openai import OpenAI


def _detect_media_type(data: bytes) -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def prepare_image_url(image_input: Any) -> str:
    if isinstance(image_input, bytes):
        if not image_input:
            raise ValueError("file_content không được rỗng")
        media_type = _detect_media_type(image_input)
        encoded = base64.b64encode(image_input).decode("ascii")
        return f"data:{media_type};base64,{encoded}"

    if isinstance(image_input, str):
        value = image_input.strip()
        if not value:
            raise ValueError("file_content không được rỗng")
        if value.startswith("data:image/"):
            return value
        if os.path.isfile(value):
            with open(value, "rb") as image_file:
                return prepare_image_url(image_file.read())
        try:
            decoded = base64.b64decode(value, validate=True)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                "file_content phải là bytes ảnh, data URI, base64 hoặc đường dẫn file ảnh"
            ) from exc
        return prepare_image_url(decoded)

    raise TypeError("file_content phải là bytes hoặc string ảnh hợp lệ")


def call_llm(model_cfg: Dict[str, Any], prompt: str, image_input: Any) -> str:
    """Send the original image and extraction prompt to an OpenAI-compatible VLM."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Prompt không được rỗng")

    client = OpenAI(
        api_key=model_cfg["api_key"],
        base_url=model_cfg["base_url"],
    )
    response = client.chat.completions.create(
        model=model_cfg["model"],
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt.strip()},
                    {
                        "type": "image_url",
                        "image_url": {"url": prepare_image_url(image_input)},
                    },
                ],
            }
        ],
        temperature=0.0,
        max_tokens=4000,
    )

    content = response.choices[0].message.content
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Model VLM không trả về nội dung")
    return content.strip()
