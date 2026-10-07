# Danh mục kết quả đã thực thi

Sinh từ các bản ghi hiện có bằng `report/audit_submission.py`; không gọi API, không sửa raw record.

## Lượt Groq thật

Cả 13 lượt dưới đây có lỗi thực thi. Điểm raw không chứng minh chất lượng model; không có bản ghi thay thế cho lượt chưa chạy.

| Run / trace | Tác vụ | Điểm raw | Token | Giây | Loại lỗi |
|---|---|---:|---:|---:|---|
| [attempts/groq-120b-code-learn](../results/attempts/groq-120b-code-learn/run.json) · [trace](../results/attempts/groq-120b-code-learn/trace.md) | code-learn | 0/10 | 0 | 10.6 | OpenAIInvalidRequestError |
| [attempts/groq-120b-data-learn](../results/attempts/groq-120b-data-learn/run.json) · [trace](../results/attempts/groq-120b-data-learn/trace.md) | data-learn | 0/8 | 7,917 | 30.2 | OpenAIInvalidRequestError |
| [attempts/groq-120b-logs-learn](../results/attempts/groq-120b-logs-learn/run.json) · [trace](../results/attempts/groq-120b-logs-learn/trace.md) | logs-learn | 0/9 | 8,163 | 72.6 | OpenAIInvalidRequestError |
| [attempts/groq-20b-data-learn](../results/attempts/groq-20b-data-learn/run.json) · [trace](../results/attempts/groq-20b-data-learn/trace.md) | data-learn | 0/8 | 7,911 | 40.6 | OpenAIInvalidRequestError |
| [attempts/groq-qwen-data-learn-413](../results/attempts/groq-qwen-data-learn-413/run.json) · [trace](../results/attempts/groq-qwen-data-learn-413/trace.md) | data-learn | 0/8 | 17,617 | 89.2 | APIStatusError |
| [attempts/groq-qwen-data-learn-4500-overflow](../results/attempts/groq-qwen-data-learn-4500-overflow/run.json) · [trace](../results/attempts/groq-qwen-data-learn-4500-overflow/trace.md) | data-learn | 0/8 | 5,034 | 4.2 | ContextOverflowError |
| [attempts/groq-qwen-data-learn-6000-413](../results/attempts/groq-qwen-data-learn-6000-413/run.json) · [trace](../results/attempts/groq-qwen-data-learn-6000-413/trace.md) | data-learn | 0/8 | 22,681 | 112.0 | APIStatusError |
| [attempts/groq-qwen-data-learn-7000-413](../results/attempts/groq-qwen-data-learn-7000-413/run.json) · [trace](../results/attempts/groq-qwen-data-learn-7000-413/trace.md) | data-learn | 0/8 | 5,034 | 3.1 | APIStatusError |
| [attempts/groq-qwen-data-learn-paged-429](../results/attempts/groq-qwen-data-learn-paged-429/run.json) · [trace](../results/attempts/groq-qwen-data-learn-paged-429/trace.md) | data-learn | 0/8 | 101,317 | 730.7 | OpenAIRateLimitError |
| [baseline/code-learn](../results/baseline/code-learn/run.json) · [trace](../results/baseline/code-learn/trace.md) | code-learn | 0/10 | 10,248 | 77.0 | OpenAIRateLimitError |
| [baseline/data-learn](../results/baseline/data-learn/run.json) · [trace](../results/baseline/data-learn/trace.md) | data-learn | 0/8 | 85,833 | 577.4 | GraphRecursionError |
| [performance/groq-20261006T152116351268Z/iteration-1/baseline/code-learn](../results/performance/groq-20261006T152116351268Z/iteration-1/baseline/code-learn/run.json) · [trace](../results/performance/groq-20261006T152116351268Z/iteration-1/baseline/code-learn/trace.md) | code-learn | 0/10 | 6,646 | 1.6 | OpenAIRateLimitError |
| [performance/groq-20261006T152443668368Z/iteration-1/baseline/code-learn](../results/performance/groq-20261006T152443668368Z/iteration-1/baseline/code-learn/run.json) · [trace](../results/performance/groq-20261006T152443668368Z/iteration-1/baseline/code-learn/trace.md) | code-learn | 0/10 | 10,248 | 180.4 | OpenAIRateLimitError |
| **Tổng: 13 lượt** | | | **288,649** | **1929.6** | **13 có lỗi** |

## Kiểm chứng và đo ngoại tuyến

| Kết quả | Bằng chứng |
|---|---|
| Suite gốc 32 đạt; curator/worker/tools thêm 32 nhóm đạt | [verification.log](performance/verification.log), [lượt test trước đó](performance/test-results.md) |
| Driver benchmark thêm 3 nhóm đạt | [benchmark-controls.log](performance/benchmark-controls.log) |
| Statement coverage 423/467 = 90,58%; thiếu 44 dòng | [coverage.json](performance/coverage.json), [metadata](performance/coverage-summary.json) |
| Simple/code/complex: 3 lần mỗi nhóm, 9/9 đạt | [summary và đường dẫn raw](performance/offline-20261006T151924755263Z/summary.json) |
| Tải 10 graph độc lập: 10/10 đạt; không gọi API | [summary stress](performance/offline-20261006T151924755263Z/summary.json) |
| Ca complex profiling đạt; 352.503 call trong 0,511s trên main thread | [profile.txt](performance/offline-20261006T151924755263Z/profile.txt) |
| So sánh tạm: chỉ hai baseline học | [table.md](table.md) |

Scripted model quyết định đường gọi; file/shell/SQLite/checker thực thi thật. Không dùng điểm fixture làm điểm Groq. Thử kết nối model riêng trả OK dùng 101 token, đã ghi ở phụ lục REPORT; không nằm trong 13 lượt tác vụ.

## Tính toàn vẹn

[submission-audit.json](performance/submission-audit.json) giữ SHA-256 của từng run/trace, kiểm tra bảng so sánh, coverage, liên kết và các phần có sẵn so với commit gốc. Audit không thay thế pytest, không chứng nhận freeze và không tự nộp bài.
