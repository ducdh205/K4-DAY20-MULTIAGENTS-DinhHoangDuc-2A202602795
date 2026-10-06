# Lượt chẩn đoán hạ tầng

Mỗi thư mục giữ nguyên `run.json` và `trace.md` của một lượt chạy thật bị lỗi trước khi thử cấu hình khác. `configuration.json` bổ sung model, tham số và commit tương ứng, không chứa khóa API.

Các lượt này không dùng để so sánh chất lượng tác tử hoặc phân loại lỗi A–G. Theo RUBRIC, lỗi API và timeout là lỗi hạ tầng. `lab.compare` chỉ đọc các thư mục điều kiện đã biết, nên không đưa `attempts/` vào bảng chính.

Token trong các bản ghi là usage API trả về cho những lời gọi đã hoàn tất. Lời gọi bị từ chối có thể không trả usage; đây không phải số liệu hóa đơn. Tổng chi phí báo cáo cần tính cả các lượt chẩn đoán, tránh bỏ qua chi phí thử lại.

Giữ nguyên model và policy cho tất cả kết quả chính trước khi so sánh. Không chọn lại lượt chạy chỉ vì điểm thấp.
