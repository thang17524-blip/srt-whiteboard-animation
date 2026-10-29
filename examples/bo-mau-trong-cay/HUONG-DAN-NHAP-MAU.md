# Bộ mẫu đầu tiên: Trồng một cây xanh mỗi ngày

Một cảnh, video ngang 16:9, thời lượng 9 giây. Ảnh do ImageGen tạo riêng; giọng Việt tổng hợp bằng Piper cục bộ từ đúng nội dung trong `kich-ban.txt`. Không cần cài Piper hoặc tải mô hình để dùng các tệp này.

## Các tệp

- `kich-ban.txt`: lời thoại UTF-8, dùng để nhập kịch bản.
- `media/anh-trong-cay.png`: ảnh minh họa 1672 × 941, không có chữ.
- `media/giong-doc.wav`: giọng đọc tiếng Việt PCM, một kênh, 22050 Hz, khoảng 8,48 giây.
- `du-an.json`: dự án một cảnh đã điền sẵn, thời lượng 9 giây, bật bàn tay.
- `video-xem-truoc.mp4`: video đã dựng bằng bộ dựng của ứng dụng, 640 × 360, có tiếng.
- `video-xem-truoc.srt`: phụ đề riêng cho cảnh.
- `NGUON-VA-GHI-CHU.md`: nguồn giọng và ghi chú về ảnh.

## Cách nhanh nhất: mở dự án điền sẵn

1. Giải nén cả gói mẫu vào một thư mục mới, ví dụ `Documents/Video-mau-trong-cay`. Không mở JSON trực tiếp trong ZIP.
2. Mở phần mềm bằng `chay_windows.cmd` trong thư mục mã nguồn đã cài.
3. Bấm **Mở dự án**, chọn `du-an.json` bên trong bộ mẫu. Giữ thư mục `media` nằm cạnh JSON.
4. Chọn cảnh **Trồng cây và tưới nước**. Kiểm tra lời thoại, ảnh và giọng đọc đã có sẵn.
5. Bấm **Tạo video**, đợi hoàn tất, rồi **Xem trước**. Dù gói đã có video tham khảo, nút Xem trước của ứng dụng cần tạo bản xem trước cho phiên hiện tại trước.
6. Bấm **Xuất MP4**, chọn tên và thư mục đích. Video ngang xuất ở 1920 × 1080. Không chọn trùng tên `video-xem-truoc.mp4` nếu muốn giữ video tham khảo.

## Cách thực hành: nhập từng tệp

1. Bấm **Tạo dự án mới**, chọn một thư mục trống khác với thư mục bộ mẫu.
2. Bấm **Nhập kịch bản**, chọn `kich-ban.txt`. Phần mềm thêm một cảnh vào cuối danh sách.
3. Chọn cảnh trống ban đầu và bấm **Xóa cảnh**. Sau đó chọn cảnh vừa nhập có lời thoại.
4. Bấm **Thêm hình ảnh**, chọn `media/anh-trong-cay.png` trong bộ mẫu.
5. Bấm **Thêm giọng đọc**, chọn `media/giong-doc.wav`.
6. Đặt **Thời lượng (giây)** là **9**, chọn **16:9**, đánh dấu **Hiện bàn tay vẽ**.
7. Bấm **Lưu dự án** → **Tạo video** → chờ hoàn tất → **Xem trước**.
8. Nếu kết quả phù hợp, bấm **Xuất MP4**. MP4 và SRT cùng tên được lưu ở nơi bạn chọn.

Có thể đổi sang 9:16 để thử video dọc; ảnh ngang sẽ có lề trên/dưới. Bộ mẫu được thiết kế ưu tiên 16:9.

## Kịch bản

Mỗi ngày, một hành động nhỏ có thể tạo nên thay đổi lớn. Hãy bắt đầu bằng việc trồng một cây xanh và chăm sóc nó. Tưới nước đều đặn, cây sẽ lớn lên từng ngày.

## Kết quả đã kiểm tra

- JSON được mở và kiểm tra bằng mã của ứng dụng.
- Tệp kịch bản và lời thoại lưu trong JSON khớp nhau.
- WAV tạo từ kịch bản trên bằng mô hình tiếng Việt, giải mã được, có tín hiệu âm thanh. Không tuyên bố đã kiểm tra phát âm thủ công từng từ.
- Video xem trước dựng thành công, 270 hình ở 30 hình/giây, 640 × 360, có hình và tiếng cùng thời lượng 9 giây, bắt đầu tại mốc 0.
- Không cần API key để sử dụng bộ mẫu. Giọng tổng hợp có thể chưa tự nhiên như người thật.
- Phiên bản ứng dụng hiện căn nét vẽ theo thời lượng toàn cảnh, chưa căn chính xác từng từ. Phụ đề là SRT riêng, chưa xuất hiện trực tiếp trên hình.
