# requirements:
# openai

import base64
import json
import os
import urllib.request
from typing import Dict, Any, Tuple, Optional

from openai import OpenAI


def _detect_media_type(data: bytes) -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def prepare_image_data(image_input: Any) -> Tuple[str, str]:
    """Extract (media_type, base64_str) from raw bytes, base64 string, data URI, or file path."""
    if isinstance(image_input, bytes):
        if not image_input:
            raise ValueError("file_content không được rỗng")
        media_type = _detect_media_type(image_input)
        encoded = base64.b64encode(image_input).decode("ascii")
        return media_type, encoded

    if isinstance(image_input, str):
        value = image_input.strip()
        if not value:
            raise ValueError("file_content không được rỗng")
        if value.startswith("data:image/"):
            header, encoded = value.split(",", 1)
            media_type = header.split(";")[0].replace("data:", "")
            return media_type, encoded
        if os.path.isfile(value):
            with open(value, "rb") as image_file:
                return prepare_image_data(image_file.read())
        try:
            decoded = base64.b64decode(value, validate=True)
            return prepare_image_data(decoded)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                "file_content phải là bytes ảnh, data URI, base64 hoặc đường dẫn file ảnh"
            ) from exc

    raise TypeError("file_content phải là bytes hoặc string ảnh hợp lệ")


def prepare_image_url(image_input: Any) -> str:
    media_type, encoded = prepare_image_data(image_input)
    return f"data:{media_type};base64,{encoded}"


def call_openai_llm(
    model_cfg: Dict[str, Any],
    prompt: str,
    image_input: Any,
    system_prompt: Optional[str] = None,
) -> str:
    """Send extraction request using OpenAI chat completions API structure."""
    client_kwargs: Dict[str, Any] = {
        "api_key": model_cfg["api_key"],
        "base_url": model_cfg["base_url"],
    }
    if model_cfg.get("organization"):
        client_kwargs["organization"] = model_cfg["organization"]

    client = OpenAI(**client_kwargs)

    messages = []
    if system_prompt and isinstance(system_prompt, str) and system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt.strip()})

    user_content = [
        {"type": "text", "text": prompt.strip()},
        {
            "type": "image_url",
            "image_url": {"url": prepare_image_url(image_input)},
        },
    ]
    messages.append({"role": "user", "content": user_content})

    temp = float(model_cfg.get("temperature", 0.0))
    temp = max(0.0, min(2.0, temp))

    response = client.chat.completions.create(
        model=model_cfg["model"],
        messages=messages,
        temperature=temp,
        max_tokens=int(model_cfg.get("max_tokens", 4000)),
    )

    content = response.choices[0].message.content
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Model OpenAI VLM không trả về nội dung")
    return content.strip()


def call_gemini_llm(
    model_cfg: Dict[str, Any],
    prompt: str,
    image_input: Any,
    system_prompt: Optional[str] = None,
) -> str:
    """Send extraction request using Google Gemini contents/parts payload structure."""
    base_url = model_cfg["base_url"].rstrip("/")

    # Fallback to OpenAI format if base_url explicitly targets an OpenAI compatible endpoint for Gemini
    if base_url.endswith("/openai") or base_url.endswith("/v1"):
        return call_openai_llm(model_cfg, prompt, image_input, system_prompt)

    media_type, base64_data = prepare_image_data(image_input)

    parts = [
        {"text": prompt.strip()},
        {
            "inline_data": {
                "mime_type": media_type,
                "data": base64_data,
            }
        },
    ]

    payload: Dict[str, Any] = {
        "contents": [
            {
                "role": "user",
                "parts": parts,
            }
        ]
    }

    if system_prompt and isinstance(system_prompt, str) and system_prompt.strip():
        payload["system_instruction"] = {
            "parts": [{"text": system_prompt.strip()}]
        }

    temp = float(model_cfg.get("temperature", 0.0))
    temp = max(0.0, min(2.0, temp))

    payload["generationConfig"] = {
        "temperature": temp,
        "maxOutputTokens": int(model_cfg.get("max_tokens", 4000)),
    }

    api_version = model_cfg.get("api_version", "v1beta")
    model_name = model_cfg["model"]
    api_key = model_cfg["api_key"]

    endpoint = f"{base_url}/{api_version}/models/{model_name}:generateContent?key={api_key}"

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode("utf-8")
            data = json.loads(resp_body)
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("Model Gemini không trả về kết quả candidate")
            parts_res = candidates[0].get("content", {}).get("parts", [])
            if not parts_res:
                raise ValueError("Model Gemini trả về nội dung rỗng")
            return parts_res[0].get("text", "").strip()
    except Exception as exc:
        raise RuntimeError(f"Lỗi khi gọi API Gemini: {exc}") from exc


def call_anthropic_llm(
    model_cfg: Dict[str, Any],
    prompt: str,
    image_input: Any,
    system_prompt: Optional[str] = None,
) -> str:
    """Send extraction request using Anthropic Claude top-level system & image block format."""
    base_url = model_cfg["base_url"].rstrip("/")
    media_type, base64_data = prepare_image_data(image_input)

    content_blocks = [
        {"type": "text", "text": prompt.strip()},
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": base64_data,
            },
        },
    ]

    temp = float(model_cfg.get("temperature", 0.0))
    temp = max(0.0, min(1.0, temp))

    payload: Dict[str, Any] = {
        "model": model_cfg["model"],
        "max_tokens": int(model_cfg.get("max_tokens", 4000)),
        "temperature": temp,
        "messages": [
            {
                "role": "user",
                "content": content_blocks,
            }
        ],
    }

    if system_prompt and isinstance(system_prompt, str) and system_prompt.strip():
        payload["system"] = system_prompt.strip()

    anthropic_version = model_cfg.get("anthropic_version", "2023-06-01")
    endpoint = f"{base_url}/v1/messages" if not base_url.endswith("/v1/messages") else base_url

    headers = {
        "x-api-key": model_cfg["api_key"],
        "anthropic-version": anthropic_version,
        "content-type": "application/json",
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=req_data,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode("utf-8")
            data = json.loads(resp_body)
            content = data.get("content", [])
            if not content or not isinstance(content, list):
                raise ValueError("Model Claude không trả về nội dung")
            text_blocks = [b.get("text", "") for b in content if b.get("type") == "text"]
            if not text_blocks:
                raise ValueError("Model Claude không trả về block text")
            return "".join(text_blocks).strip()
    except Exception as exc:
        raise RuntimeError(f"Lỗi khi gọi API Anthropic Claude: {exc}") from exc


def call_llm(
    model_cfg: Dict[str, Any],
    prompt: str,
    image_input: Any,
    system_prompt: Optional[str] = None,
) -> str:
    """Send extraction prompt & image input to the specified LLM provider."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Prompt không được rỗng")

    provider = model_cfg.get("provider", "openai")

    if provider == "gemini":
        return call_gemini_llm(model_cfg, prompt, image_input, system_prompt=system_prompt)
    elif provider == "anthropic":
        return call_anthropic_llm(model_cfg, prompt, image_input, system_prompt=system_prompt)
    else:
        return call_openai_llm(model_cfg, prompt, image_input, system_prompt=system_prompt)
