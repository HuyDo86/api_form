import os
import base64
from typing import Dict, Any, Optional
from openai import OpenAI


def prepare_image_url(image_input: Any, default_media_type: str = "image/jpeg") -> str:
    """
    Chuyển đổi các định dạng đầu vào là ảnh (bytes, file path, base64, data URI) thành chuỗi Data URI chuẩn.
    """
    if isinstance(image_input, bytes):
        b64 = base64.b64encode(image_input).decode("utf-8")
        return f"data:{default_media_type};base64,{b64}"

    if isinstance(image_input, str):
        str_val = image_input.strip()
        if str_val.startswith("data:image"):
            return str_val
        if len(str_val) < 260 and "\n" not in str_val and os.path.exists(str_val) and os.path.isfile(str_val):
            ext = os.path.splitext(str_val)[1].lower().strip(".")
            media_type = f"image/{ext}" if ext in ["png", "jpeg", "jpg", "webp"] else default_media_type
            with open(str_val, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            return f"data:{media_type};base64,{b64}"
        if len(str_val) > 100 and not any(c in str_val for c in ["\n", " ", ":"]):
            return f"data:{default_media_type};base64,{str_val}"

    return str(image_input)


def call_llm(
    model_cfg: Dict[str, Any],
    prompt: str,
    image_input: Optional[Any] = None,
) -> str:
    """
    Gọi mô hình LLM / VLM (Multimodal Vision) trích xuất trực tiếp trong 1 bước duy nhất.
    - Nếu truyền 'image_input': Gửi đồng thời Ảnh + Prompt tới mô hình VLM để trích xuất trong 1 bước duy nhất.
    - Nếu không có ảnh: Gọi mô hình Text LLM thông thường.
    """
    client = OpenAI(
        api_key=model_cfg.get("api_key"),
        base_url=model_cfg.get("base_url"),
    )

    model_name = model_cfg.get("model") or "deepseek/deepseek-chat"

    # Nếu có truyền ảnh, sử dụng Vision Message Payload (1 bước duy nhất VLM)
    if image_input is not None:
        image_url = prepare_image_url(image_input)
        if image_url.startswith("data:image"):
            content_payload = [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": image_url}
                }
            ]
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": content_payload}],
                temperature=0.0,
                max_tokens=4000,
            )
            return response.choices[0].message.content

    # Mặc định gọi Text LLM
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=4000,
    )

    return response.choices[0].message.content