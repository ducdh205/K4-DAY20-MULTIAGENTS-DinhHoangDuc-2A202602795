# Checklist bản nộp

Đối chiếu ngày 07/10/2026 theo [README](../README.md), [GUIDE](../GUIDE.md) và [RUBRIC](../RUBRIC.md). Báo cáo đã trình bày kết quả hiện có; **thí nghiệm chính chưa hoàn tất**. Không tự chấm điểm hoặc đánh dấu lượt chưa chạy là đạt.

## Sản phẩm và bằng chứng

| Yêu cầu repo | Trạng thái | Bằng chứng / việc còn thiếu |
|---|---|---|
| Môi trường, model, tour | Đã kiểm chứng ở Phần 0 | Phụ lục [REPORT](REPORT.md); 15 test provided đạt; kết nối OK riêng 101 token. |
| Năm hàm TODO trong bốn module | Đã triển khai | `src/lab/{agent,subagents,runner,curator}.py`; suite gốc 32/32 đạt. |
| Công cụ, giao tiếp, log, lỗi worker | Đã kiểm chứng ngoại tuyến | 14 nhóm worker + 14 nhóm tools; graph fixture dùng công cụ thật, không gọi API. |
| Curator và driver benchmark | Đã kiểm chứng ngoại tuyến | 4 nhóm curator + 3 nhóm driver; [log kiểm chứng](performance/verification.log), [log driver](performance/benchmark-controls.log). |
| Coverage và đo hiệu suất | Có số liệu ngoại tuyến | 90,58% statement; 9 lượt tuần tự, 10 graph đồng thời, 1 ca profiling. Không đại diện latency/chất lượng Groq. |
| Đủ baseline và taxonomy chất lượng | Còn thiếu | Bảng chính có 2 baseline học bị lỗi; thiếu logs học và 3 eval. Chẩn đoán riêng không dùng để lấp kết quả khác cấu hình. |
| Đủ subagents và phân tích vết thật | Còn thiếu | Chưa có kết quả model thật cho điều kiện này. |
| Skill curator thật, đánh giá skill, skills-auto học | Còn thiếu | Chưa có feedback dùng được; `skills/auto/` chỉ có README. Không sửa tay skill. |
| H1–H3 trước freeze | Đã viết và commit | Commit `102da2b`, thông điệp `hypotheses`; H1–H3 là dự đoán, chưa kiểm chứng. |
| Freeze và eval chính thức | Còn thiếu | Chưa tạo tag; chưa chạy đánh giá. Chưa có kết quả `verify_freeze.py` OK. |
| Bảng ba điều kiện/sáu tác vụ | Còn thiếu | [table.md](table.md) đúng với dữ liệu hiện có nhưng mới có hai baseline học. |
| Báo cáo 10 mục, hạn chế, lệnh tái lập | Đã hoàn thiện cho dữ liệu hiện có | [REPORT](REPORT.md), [danh mục bằng chứng](RESULTS_INDEX.md). Phân tích nêu rõ câu hỏi chưa thể kết luận. |
| Bonus theo GUIDE | Chưa thực hiện | Chỉ tính sau hạng mục chính; không nhận đo tải fixture là bonus pooling hoặc lặp eval. |
| `.env` riêng tư; phần có sẵn nguyên vẹn | Audit ngoại tuyến | [submission-audit.json](performance/submission-audit.json): Git ignore, không tracked `.env`, đối chiếu protected files/AST với `ad29c55`, quét mẫu credential mà không in nội dung. |
| Push GitHub | Đã thực hiện | Bản báo cáo Phần 6 tại commit `0047f33` đã push lên `origin/main`; `.env` không nằm trong lịch sử Git. |
| Nộp lên hệ thống lớp | Chưa thực hiện | Chưa có URL/các trường của trang nộp; xuất bản kho chưa đồng nghĩa hoàn thành thí nghiệm hoặc đã bấm nộp trên hệ thống lớp. |

## Liên kết dùng để nộp

- [Kho mã nguồn](https://github.com/ducdh205/K4-DAY20-MULTIAGENTS-DinhHoangDuc-2A202602795).
- [Báo cáo](https://github.com/ducdh205/K4-DAY20-MULTIAGENTS-DinhHoangDuc-2A202602795/blob/main/report/REPORT.md).
- [Danh mục kết quả và vết](https://github.com/ducdh205/K4-DAY20-MULTIAGENTS-DinhHoangDuc-2A202602795/blob/main/report/RESULTS_INDEX.md).

Mô tả tình trạng bài: đã triển khai harness/subagent/curator, 32 test gốc và 35 nhóm kiểm chứng bổ sung đạt; coverage 90,58%. Có 13 lượt Groq thật bị lỗi thực thi được lưu và phân tích. Benchmark ba điều kiện, skill thật, freeze và eval còn thiếu; báo cáo không khẳng định lab đã hoàn tất hay tự nhận điểm thưởng.

## Đối chiếu 10 nội dung trong checklist tham khảo

Giữ thứ tự 10 mục của REPORT_TEMPLATE trong repo; các chủ đề của bản tham khảo được đặt ở vị trí dưới đây.

| Chủ đề tham khảo | Vị trí trong REPORT |
|---|---|
| Tổng quan, goal, scope | Mục 1 |
| Sơ đồ, component, protocol, message flow | Mục 3 và mục 5 |
| Implementation, quyết định, trade-off | Mục 5: Quyết định triển khai và khả năng phục hồi |
| Unit/integration/E2E fixture, lỗi, coverage | Mục 5 và log kiểm chứng |
| Latency, throughput, resource, bottleneck | Mục 5; RAM/CPU/utilization được ghi chưa đo |
| Error và resilience | Mục 4 và bảng lỗi mục 5 |
| Design so với implementation | Mục 8 |
| Scalability | Mục 8 |
| Hạn chế và tính hợp lệ | Mục 9 |
| Kết luận, bước tiếp theo | Mục 10 và checklist dưới đây |

## Việc tiếp theo để hoàn tất thí nghiệm

1. Khi quota Groq khả dụng, tiếp tục các lượt học cùng cấu hình, lưu mỗi lượt vào thư mục riêng và cập nhật ledger. Quyền đã có cho tối đa 18 lượt Phần 5; 2 đã thử, 16 chưa thực thi. Quyền này không bao gồm tự mở rộng số lượt hay chạy eval.
2. Từ lượt baseline học dùng được, phân loại check và chạy curator; đánh giá skill thật, chạy skills-auto học, lưu bản sao kết quả trước freeze. Nếu học lại làm thay đổi căn cứ H1–H3, ghi rõ và commit giả thuyết cập nhật trước freeze.
3. Chốt skill, commit `freeze skills`, tạo tag `freeze`; chỉ sau đó thực hiện các lượt đánh giá được cho phép. Chạy `verify_freeze.py`, `lab.compare` và `check_breakdown.py`, cập nhật bảng và phân tích từ raw record.
4. Chỉ chọn một bonus trong GUIDE sau khi phần chính hoàn tất; cần thiết kế riêng và số liệu model thật. Các ví dụ pooling/cache/dashboard của bản tham khảo không thay thế tiêu chí bonus repo.
5. Kiểm tra bảo mật, diff, audit và commit bản cập nhật; push kho đã xác nhận rồi nộp liên kết theo kênh lớp cung cấp.

## Tái lập kiểm tra bản nộp hiện tại

Chạy tại gốc repo trong WSL bằng `.venv/bin/python`:

```bash
.venv/bin/python report/audit_submission.py
git diff --check
git status --short
```

Audit chỉ đối chiếu bằng chứng đã lưu; không gọi mô hình, không đọc trực tiếp check/kết quả eval trước freeze, không sửa raw records. Lệnh kiểm chứng đầy đủ và đo coverage đã thực thi được ghi trong phụ lục REPORT; không cần chạy API để xem bản nộp.
