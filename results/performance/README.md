# Benchmark học thật — Phần 5 tham khảo

Hai thư mục là lượt chạy Groq thật bằng harness revision `9b49902`, model `qwen/qwen3.8-27b`, temperature 0, profile input 7000, output 900, recursion limit 20, SDK retry 0. Mỗi thư mục có cấu hình, manifest, `run.json` và `trace.md` do runner ghi; không sửa số liệu sau khi chạy.

| Thư mục | Điều kiện/tác vụ | Pacing mỗi lần gọi model | Token ghi nhận | Giây | Kết quả |
|---|---|---|---:|---:|---|
| `groq-20261006T152116351268Z` | baseline/code-learn | Không pacing | 6.646 | 1,6 | 429 theo phút |
| `groq-20261006T152443668368Z` | baseline/code-learn | 60 giây | 10.248 | 180,4 | 429 theo ngày |

Người dùng cho phép tối đa 18 lượt ở giai đoạn này; đã thử 2, còn 16 chưa chạy. Manifest thứ nhất dự kiến 18 lượt; lần thử tiếp giảm cap còn 17 để tính lượt lỗi đầu vào trần chung. Batch dừng ở lỗi provider, không đánh dấu các lượt chưa chạy thành kết quả 0.

Các cặp tác vụ/điều kiện chưa có ba lần lặp. Điểm raw 0/10 của hai lượt lỗi không phải bằng chứng chất lượng agent. Không có kết quả eval hoặc skill sinh ra trong bước này.

Thư mục được đặt riêng để `lab.compare` mặc định tiếp tục đọc dữ liệu baseline lịch sử ở `results/baseline/`; kết quả diagnostic mới nằm trong mục 5 của báo cáo. Muốn đối chiếu bảng raw của từng iteration, dùng `lab.compare --results <batch>/iteration-1`; không so latency các lượt lỗi với SLA tác vụ thành công.
