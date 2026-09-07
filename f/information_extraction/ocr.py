#requirements:
#openai==1.54.0
#wmill
#httpx==0.27.2
import wmill
import base64
from datetime import datetime, timezone, timedelta
from openai import OpenAI

VN_TZ = timezone(timedelta(hours=7))

OCR_PROMPT = """Bạn là một chuyên gia OCR cao cấp chuyên trích xuất nội dung từ các hình ảnh chứng từ kế toán, tài chính, kho vận và hành chính tại Việt Nam.

Hệ thống nhận diện chính xác 13 loại chứng từ sau:
1. Phiếu thu
2. Phiếu chi
3. Phiếu nhập kho
4. Phiếu xuất kho
5. Hóa đơn (Hóa đơn GTGT / Hóa đơn bán hàng / Hóa đơn điện tử)
6. Báo giá
7. Chuyển khoản ngân hàng (Giấy báo Nợ, Giấy báo Có, Ủy nhiệm chi, Biên lai chuyển tiền)
8. Yêu cầu thanh toán (Giấy đề nghị thanh toán)
9. Phiếu nộp thuế (Giấy nộp tiền vào Ngân sách Nhà nước)
10. Phiếu giao nhận hàng hóa (Biên bản giao nhận vật tư / hàng hóa)
11. Phiếu giao nhận bê tông (Phiếu xuất xưởng / giao bê tông thương phẩm)
12. Vận đơn (Phiếu vận chuyển / Waybill / Biên bản giao hàng đường bộ)
13. Biên bản làm việc (Biên bản cuộc họp / Biên bản nghiệm thu / Biên bản bàn giao)

YÊU CẦU TRÍCH XUẤT ĐẶC BIỆT:

1. XỬ LÝ ẢNH MỜ / CHỮ VIẾT TAY / CHẤT LƯỢNG KÉM:
   - Phân tích kỹ các nét chữ mờ, mờ nhạt hoặc chữ viết tay. Dựa vào ngữ cảnh kế toán (như phép tính tổng số tiền, mã số thuế, mác bê tông, ngày tháng) để luận giải chính xác các con số và từ ngữ bị mờ.
   - Nếu có từ/số bị mờ hoàn toàn không thể đọc chắc chắn, hãy ghi nhận `[không rõ]` hoặc `[chữ mờ]` đúng vị trí, tuyệt đối không tự bịa đặt.

2. XỬ LÝ ẢNH LỚN / ĐỘ PHÂN GIẢI CAO / NHIỀU CHI TIẾT:
   - Đọc và trích xuất TOÀN BỘ văn bản từ trên xuống dưới, từ trái sang phải, không bỏ qua bất kỳ vùng dữ liệu nào (kể cả đầu trang, chân trang, ghi chú góc, con dấu, số chứng từ, ngày tháng).
   - Giữ nguyên cấu trúc bảng biểu (`| header | header |`, `|---|---|`), ghi nhận đầy đủ từng dòng sản phẩm, đơn giá, thành tiền, thuế suất, mác bê tông, khối lượng, v.v.

3. XỬ LÝ NHIỀU PHIẾU / NHIỀU CHỨNG TỪ TRONG CÙNG 1 ẢNH:
   - Nếu ảnh chứa nhiều phiếu/chứng từ (ví dụ: chụp ghép 2-3 phiếu thu/chi/giao hàng cạnh nhau hoặc trên dưới):
   - Phân tách rõ ràng từng chứng từ bằng đường phân cách `---` và gắn tiêu đề `## Chứng từ 1`, `## Chứng từ 2`,...
   - Trích xuất đầy đủ nội dung của TẤT CẢ các phiếu xuất hiện trong ảnh."""


def main(
    file_content: bytes,
    media_type: str = "image/jpeg",
    vlm_resource: dict = wmill.get_resource("f/information_extraction/qwen_vlm"),
) -> dict:

    ocr_start = datetime.now(VN_TZ)

    client = OpenAI(
        api_key=vlm_resource["api_key"],
        base_url=vlm_resource["base_url"],
    )

    b64_data = base64.b64encode(file_content).decode("utf-8")

    response = client.chat.completions.create(
        model=vlm_resource.get("model", "5CD-AI/Vintern-3B-R-beta"),
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": OCR_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{media_type};base64,{b64_data}"}
                },
            ],
        }],
        max_tokens=4000,
        temperature=0.0,
    )

    markdown_text = response.choices[0].message.content
    ocr_end = datetime.now(VN_TZ)

    return {
        "markdown_text": markdown_text,
        "ocr_duration_seconds": round((ocr_end - ocr_start).total_seconds(), 2),
    }