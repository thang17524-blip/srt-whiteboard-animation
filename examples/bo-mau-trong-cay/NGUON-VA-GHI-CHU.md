# Nguồn và ghi chú

## Kịch bản

Kịch bản tiếng Việt được viết mới cho bộ mẫu “Trồng một cây xanh mỗi ngày”. Nội dung là một lời gợi ý ngắn về chăm sóc cây, không nhằm hướng dẫn kỹ thuật trồng cây cụ thể.

## Ảnh minh họa

Ảnh được tạo mới bằng công cụ ImageGen tích hợp, không dùng API key bên ngoài. Tệp gốc được giữ nguyên trong bộ mẫu, không chỉnh sửa sau khi tạo.

Nội dung yêu cầu tạo ảnh: minh họa ngang 16:9 cho hoạt hình bảng vẽ; một em nhỏ quỳ tưới cây non; đường viền màu than rõ, nét tối giản, khoảng trống thoáng; nền giấy kem #F6F1E3; điểm nhấn xanh lam và cam; không có chữ, số, logo, bàn tay cầm bút hay hình ba chiều. Ảnh diễn đạt nội dung lời thoại về trồng và chăm sóc cây. Kết quả thực tế có sắc nâu ở thân cây và tô màu quần áo, phù hợp để thử chế độ vẽ rồi lên màu của ứng dụng.

## Giọng đọc

- Công cụ: Piper TTS 1.8.0, chạy cục bộ bằng CPU.
- Mô hình: `vi_VN-vais1000-medium`, một giọng tiếng Việt, 22050 Hz.
- Nguồn mô hình: https://huggingface.co/rhasspy/piper-voices/tree/main/vi/vi_VN/vais1000/medium
- Thẻ mô hình: https://huggingface.co/rhasspy/piper-voices/blob/main/vi/vi_VN/vais1000/medium/MODEL_CARD
- Thẻ mô hình dẫn nguồn dữ liệu VAIS-1000 và giấy phép CC BY 4.0: https://creativecommons.org/licenses/by/4.0/
- Dữ liệu gốc: https://ieee-dataport.org/documents/vais-1000-vietnamese-speech-synthesis-corpus
- Mã nguồn Piper: https://github.com/OHF-Voice/piper1-gpl

Thay đổi thực hiện: dùng mô hình để tổng hợp lời thoại mới của bộ mẫu, hệ số độ dài 1,05 và khoảng nghỉ câu 0,35 giây. Không nhân bản giọng của người dùng, không gọi API trả phí. Không phân phối kèm mô hình hoặc bộ chạy Piper trong gói này; gói chỉ có WAV đã tổng hợp.

## Video tham khảo

Video xem trước được dựng bằng mã Giai đoạn 2 của dự án srt-whiteboard-animation. Tài sản bàn tay gốc và dấu hiệu trên bút được giữ nguyên. Ảnh minh họa có nét đậm và vùng tô màu nên bộ dựng có thể tạo viền hoặc tô lại theo lưới; đây là mẫu thực hành phiên bản đầu, không phải cam kết chất lượng xuất bản chuyên nghiệp.
