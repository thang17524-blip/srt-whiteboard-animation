# Báo cáo Giai đoạn 2 — phiên bản đầu

Ngày kiểm tra: 29/10/2026. Kho: `thang17524-blip/srt-whiteboard-animation`.
Nhánh phát triển: `feat/windows-vietnamese-studio`, bắt đầu từ `696a7243c0e6ffb6827676e539c2ca5ebae2bf6b`. Không sửa trực tiếp `main`.

## Chức năng đã triển khai và kiểm thử

- Giao diện desktop tiếng Việt bằng Tkinter đi kèm Python, có đủ bảy nút được yêu cầu.
- Tạo, lưu và mở dự án JSON; sao chép tài sản vào thư mục dự án.
- Nhập kịch bản TXT/SRT; thêm, sửa, xóa và đổi thứ tự cảnh.
- Thêm ảnh và giọng đọc có sẵn; lấy thời lượng từ số mẫu âm thanh; từ chối thời lượng làm cắt lời đọc.
- Khung hình ngang 1920 × 1080 và dọc 1080 × 1920, H.264/AAC, 30 hình/giây.
- Giữ tỷ lệ ảnh bằng lề màu kem, giữ chung màu giấy và tài sản bàn tay gốc.
- Tạo MP4 xem trước 640 × 360 / 360 × 640 bằng cùng bộ dựng, không dùng hiệu ứng mở hình chữ nhật.
- Tạo video trong luồng nền, báo tiến độ và hủy. Hủy giữa chừng không thay tệp MP4 cũ.
- Xuất SRT riêng: một mục cho lời thoại của mỗi cảnh.
- Nhập JSON vùng vẽ gốc; kiểm tra kích thước, vùng vượt biên, thời gian chồng lấn, dữ liệu không hữu hạn và thời lượng cảnh.
- Sửa lỗi thừa đối số ở nhánh không có nét; bổ sung số khung hình khi vùng bị che hoàn toàn.
- Chuẩn hóa số khung hình để không tự kéo dài video ngoài thời lượng đã kiểm tra.
- Sửa duyệt gói mã hóa PyAV trong chuyển mã H.264.
- Ghép bằng FFmpeg có chuẩn hóa tỷ lệ, tốc độ hình và âm thanh; nhánh PyAV dự phòng báo lỗi nếu có âm thanh để không âm thầm làm mất tiếng.
- Giữ toàn bộ công cụ gốc. Trình chỉnh HTML cập nhật lịch vẽ khi đổi thứ tự danh sách.

## Bằng chứng kiểm thử thực tế

Môi trường: Windows, Python 3.13.17 64-bit; bộ phiên bản trong `requirements-tested-windows.txt`.

1. Chạy toàn bộ bộ kiểm thử khi có 14 trường hợp: **14/14 đạt trong 110,159 giây**.
2. Bổ sung kiểm thử nút thêm giọng đọc và xuất MP4 qua Tk; chạy lại nhóm giao diện: **4/4 đạt trong 2,616 giây**. Hiện có tổng cộng **15 trường hợp kiểm thử duy nhất**, tất cả đã chạy đạt.
3. Tạo và giải mã hai video Full HD thật, mỗi video 36 hình ở 30 hình/giây; xác nhận kích thước chính xác, H.264, có âm thanh AAC và tín hiệu âm thanh khác im lặng. Tín hiệu thử là sóng âm tổng hợp, không phải giọng AI.
4. Kiểm tra khung đầu sạch, khung cuối có hình, vùng tương lai bị che; xem trực tiếp các ảnh khung giữa có tài sản bàn tay ở cả hai tỷ lệ.
5. Ghép video nhiều cảnh, kiểm tra số hình và SRT; kiểm tra đường dẫn có dấu tiếng Việt và dấu nháy đơn.
6. Kiểm tra hủy trước khi dựng và hủy trong lúc ghi hình; tệp MP4 cũ được giữ và thư mục tạm được dọn.
7. Widget Tk thật được khởi tạo; callback nhập ảnh, giọng, SRT, lưu, sắp xếp, tạo bản xem trước và xuất Full HD đã được thực thi. Hộp chọn tệp và lệnh mở trình phát ngoài được thay bằng mock để kiểm thử lặp lại.
8. Lệnh gốc `render_stream_whiteboard.py` chạy trên ảnh và JSON ví dụ thật ở chế độ skeleton, 320 × 180, 12 hình/giây, xuất MP4 thành công. Lệnh tạo ảnh kiểm tra vùng gốc cũng chạy thành công.
9. `pip check`, phân tích cú pháp toàn bộ tệp Python và `git diff --check` đều đạt.

Kiểm tra môi trường xác nhận Tcl/Tk, H.264, AAC và FFmpeg có sẵn. Sandbox không khởi tạo được Tcl; nhóm giao diện đã chạy lại thành công ngoài sandbox. Công cụ chụp cửa sổ Windows bị hết thời gian hai lần, vì vậy **chưa xác nhận trực quan toàn bộ bố cục giao diện bằng ảnh chụp**, và chưa xác nhận phát âm thanh qua trình phát mặc định bằng thao tác thủ công. Không coi việc kiểm thử callback mở trình phát là bằng chứng đã nghe được lời đọc.

Workflow GitHub Actions Windows được bổ sung; kết quả chạy cục bộ ở trên không thay thế trạng thái CI từ GitHub. Chưa xác nhận cài đặt trên một máy Windows sạch khác; các tệp CMD đã được cung cấp nhưng chưa tự động chạy toàn bộ bộ cài tương tác từ đầu.

## Chưa hoàn thành / giới hạn

- Chưa có AI viết kịch bản, tạo ảnh, phân vùng ngữ nghĩa hoặc tạo giọng tiếng Việt. Không gọi dịch vụ trả phí, không có API key.
- Chưa có căn chỉnh theo từ hoặc theo sự kiện lời thoại; hiện co lịch vẽ theo thời lượng cảnh. SRT nhập được gom theo thời gian và không giữ nguyên từng mốc phụ đề khi xuất lại.
- Chưa có nhạc nền, hiệu ứng âm thanh hoặc phụ đề ghi trực tiếp lên hình.
- Chưa có bộ cài EXE độc lập; cần Python và chạy hai tệp CMD.
- Chưa có trình chỉnh vùng đồ họa tiếng Việt trong ứng dụng. Có thể nhập JSON; trình chỉnh HTML gốc vẫn được giữ nguyên ngôn ngữ chính.
- Bàn tay dùng tài sản minh họa có sẵn, không phải cảnh quay bàn tay người thật; giữ nguyên dấu hiệu trên tài sản gốc, chưa thêm xoay cổ tay hoặc chuyển động đa tư thế.
- Xem trước và xuất dùng chung thuật toán nhưng khác độ phân giải nên đường nét lấy mẫu có thể khác; xem trước phát bằng trình phát mặc định bên ngoài ứng dụng.
- Chưa có phục hồi tác vụ sau khi máy tắt, tăng tốc GPU, đánh giá video dài hoặc kiểm thử nhiều cấu hình Windows.

## Sử dụng

Đọc `HUONG_DAN_WINDOWS.md`. Chạy `cai_dat_windows.cmd`, rồi `chay_windows.cmd`.
Tạo dự án → thêm cảnh/kịch bản → thêm ảnh → thêm giọng đọc → Tạo video → Xem trước → Xuất MP4.

## Đề xuất bước tiếp theo

Ưu tiên nghiệm thu trên máy Windows sạch và hoàn thiện trình chỉnh cảnh/vùng tiếng Việt. Sau đó thử nghiệm bộ tạo giọng tiếng Việt, căn lời thoại, thêm nhạc/phụ đề trên hình và mới tích hợp AI kịch bản/ảnh qua mô-đun có thể thay thế.
