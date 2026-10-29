# Xưởng video vẽ tay — bản đầu cho Windows

Ứng dụng chạy cục bộ, dùng ảnh và giọng đọc có sẵn. Không cần API key và không gọi API trả phí. Chưa có AI viết kịch bản, tạo ảnh hoặc tạo giọng đọc.

## Cài đặt

1. Cài Python 64-bit từ https://www.python.org/downloads/windows/, khuyến nghị Python 3.13. Bật **Add Python to PATH**, giữ thành phần **Tcl/Tk and IDLE**.
2. Tải nhánh phát triển hoặc phiên bản đã hợp nhất của dự án và giải nén vào thư mục có quyền ghi.
3. Chạy `cai_dat_windows.cmd`. Cần Internet lần đầu để tải thư viện và FFmpeg đi kèm imageio-ffmpeg. Không cần mua dịch vụ hoặc cài FFmpeg vào PATH.
4. Chạy `chay_windows.cmd`.

Nếu PowerShell đang mở trong thư mục dự án, cũng có thể chạy:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\kiem_tra_moi_truong.py
.\.venv\Scripts\python.exe chay_ung_dung.py
```

Không cần kích hoạt môi trường bằng Activate.ps1. Không cần thay đổi chính sách thực thi PowerShell.

## Tạo video

1. Bấm **Tạo dự án mới** và chọn một thư mục trống. Dữ liệu lưu trong `du-an.json`, tài sản được sao chép vào `media/`.
2. Nhập lời thoại vào ô kịch bản. **Nhập kịch bản** nhận TXT UTF-8 (mỗi đoạn cách nhau bằng dòng trống thành một cảnh) hoặc SRT (gom theo thời lượng khoảng 30 giây, không phân tích ngữ nghĩa). Các cảnh được thêm vào cuối danh sách. Có thể xóa cảnh trống ban đầu.
3. Chọn từng cảnh, bấm **Thêm hình ảnh**. Nên dùng PNG/JPG đường nét rõ, nền sáng, ảnh đủ lớn. Ảnh được giữ tỷ lệ, thêm lề màu kem; ảnh ngang trong video dọc sẽ có lề trên/dưới.
4. Bấm **Thêm giọng đọc** để thêm WAV, MP3 hoặc định dạng được hỗ trợ. Thời lượng cảnh tự điều chỉnh theo tệp âm thanh. Mỗi cảnh dùng một tệp giọng đọc. Cảnh không có giọng đọc dùng âm thanh im lặng.
5. Sửa tên, kịch bản, thời lượng; thêm, xóa hoặc di chuyển cảnh. Khi nhập thời lượng, dùng dấu phẩy hoặc dấu chấm thập phân. Nếu thời lượng ngắn hơn giọng đọc, phần mềm báo lỗi để tránh cắt tiếng.
6. Chọn **16:9** hoặc **9:16**, bật/tắt bàn tay. Bàn tay và màu giấy dùng chung cho toàn dự án.
7. Bấm **Tạo video**: dựng bản xem trước 640 × 360 hoặc 360 × 640, 30 hình/giây. Tiến độ cập nhật ở cuối cửa sổ, có nút **Hủy xử lý**.
8. Khi hoàn tất, bấm **Xem trước**: mở MP4 thật bằng trình phát mặc định Windows, có âm thanh. Đây là bản dựng nét vẽ, không phải hiệu ứng mở vùng hình chữ nhật. Nếu thay đổi dự án, cần tạo lại bản xem trước.
9. Bấm **Xuất MP4** để dựng bản Full HD: **1920 × 1080** hoặc **1080 × 1920**, H.264, AAC, 30 hình/giây. Một tệp SRT cùng tên được tạo cạnh MP4; mỗi cảnh là một mục phụ đề. Phụ đề chưa được ghi trực tiếp lên hình.

**Lưu dự án** ghi thay đổi vào JSON. Chuyển sang dự án khác hoặc đóng ứng dụng sẽ lưu dự án hiện tại. Muốn di chuyển sang máy khác, sao chép cả thư mục dự án gồm JSON và `media/`.

## Vùng vẽ nâng cao và các chức năng gốc

Mặc định, mỗi ảnh là một vùng vẽ. Không có phân vùng ngữ nghĩa tự động trong phiên bản này. Dùng **Nhập vùng vẽ JSON** nếu có `annotation.json` theo định dạng gốc; `canvas` phải đúng kích thước ảnh sau áp dụng hướng EXIF. Các vùng phải nằm trong ảnh, không chồng lấn thời gian; cảnh cần ít nhất 0,5 giây dừng cuối. Lịch vẽ được co theo thời lượng cảnh khi nhập vào ứng dụng.

Trình chỉnh vùng gốc `assets/preview.html` và các lệnh `parse_srt.py`, `render_stream_whiteboard.py`, `merge_scenes.py` vẫn được giữ. Trình HTML gốc vẫn bằng tiếng Trung và dùng xem trước hình chữ nhật; giao diện desktop tiếng Việt là lối sử dụng mới. Có thể dùng Chrome/Edge để mở trình HTML khi cần sửa vùng chi tiết rồi nhập JSON trở lại ứng dụng.

## Xử lý lỗi

- **Thiếu thư viện:** chạy lại `cai_dat_windows.cmd`. Nếu có lỗi mạng, kiểm tra Internet và chạy lại; không nhập API key vào mã nguồn.
- **Thiếu Tk:** dùng bộ cài Python chính thức và thêm thành phần Tcl/Tk.
- **Ảnh không đọc được:** thử mở ảnh bằng Photos, lưu lại PNG/JPG và thêm lại.
- **Tệp âm thanh không đọc được:** thử WAV PCM hoặc MP3; kiểm tra tệp có âm thanh thật.
- **Thiếu tệp khi mở dự án:** khôi phục thư mục `media/` hoặc thêm lại tài sản bị thiếu.
- **Chưa xem trước được:** chờ tạo video hoàn tất; cài/chọn trình phát mặc định hỗ trợ MP4 H.264/AAC.
- **Chậm khi xuất:** thử bản xem trước trước, giảm độ phức tạp ảnh và dùng thời lượng ngắn. Không có tăng tốc GPU trong bản đầu.
- **Không ghi được đầu ra:** chọn thư mục có quyền ghi, đóng tệp đang mở trong trình phát rồi thử lại.
- **FFmpeg riêng:** có thể đặt biến môi trường `WHITEBOARD_FFMPEG` tới tệp `ffmpeg.exe` có H.264 và AAC. Nếu không đặt, dùng FFmpeg trong PATH hoặc imageio-ffmpeg.

## Kiểm thử

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

Kiểm thử tạo và giải mã video thật, gồm cả Full HD, nên có thể mất vài phút. Dùng âm thanh tổng hợp để kiểm tra bảo toàn tiếng; không đánh giá chất lượng giọng đọc tiếng Việt. Chi tiết kết quả thực tế nằm trong `BAO_CAO_GIAI_DOAN_2.md`.

## Giấy phép

Giữ MIT và thông tin tác giả của dự án gốc. Python/Tk, NumPy, OpenCV, Pillow, PyAV và imageio-ffmpeg là các thành phần miễn phí/mã nguồn mở. FFmpeg đi kèm có các thành phần với nghĩa vụ giấy phép riêng (bao gồm bản dựng có GPL/libx264); khi phân phối lại thư viện hoặc bộ cài cần giữ thông báo giấy phép tương ứng. Phiên bản này không kèm mô hình AI hoặc dịch vụ thương mại.
