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

## Usage theo tác vụ và nhóm lỗi thực thi

Cộng cả các lượt chẩn đoán khác cấu hình để kiểm toán usage; không dùng làm mean score của điều kiện.

| Tác vụ | Lượt có lỗi / đã chạy | Input token | Output token | Tổng token | Tổng giây | Tool call chính |
|---|---:|---:|---:|---:|---:|---:|
| code-learn | 4/4 | 26.602 | 540 | 27.142 | 269,6 | 19 |
| data-learn | 8/8 | 233.744 | 19.600 | 253.344 | 1.587,4 | 45 |
| logs-learn | 1/1 | 8.042 | 121 | 8.163 | 72,6 | 3 |
| **Tổng** | **13/13** | **268.388** | **20.261** | **288.649** | **1.929,6** | **67** |

| Nhóm lỗi thực thi | Số lượt | Tỷ lệ trong 13 lượt |
|---|---:|---:|
| provider-request-or-transport | 8 | 61.54% |
| provider-rate-limit | 4 | 30.77% |
| graph-iteration-limit | 1 | 7.69% |

## Check raw của hai baseline chính

Check dưới đây được chấm sau khi lượt đã dừng ở quota/guardrail. Không phân loại chúng thành lỗi chất lượng A–G; `tests_not_modified=false` là check trong workspace tác vụ, không phải bằng chứng thư mục tests của repo đã bị sửa. Audit Git xác nhận các tệp có sẵn nguyên vẹn.

### code-learn: 0/10

Nguồn: [run.json](../results/baseline/code-learn/run.json), [trace](../results/baseline/code-learn/trace.md). Detail trích tối đa 160 ký tự; xem bản gốc để đọc đầy đủ.

| Check | Passed (raw) | Detail trích ngắn |
|---|---|---|
| `visible_suite_passes` | false | 2 failed, 4 passed in 3.04s |
| `tests_not_modified` | false | the original files in tests/ must not be modified (new test files are allowed) |
| `parse_price_all_formats` | false | wrong for: ['$1,299.50', '(12.00)', '$1,000,000.00'] |
| `other_caller_fixed` | false | to_csv_row returned '&lt;InvalidOperation&gt;' |
| `discount_rounds_half_up` | false | wrong for: [('10.05', 10, '9.05'), ('0.05', 50, '0.03'), ('2.665', 0, '2.67')] |
| `low_stock_follows_docstring` | false | low_stock returned ['b', 'A', 'c'] |
| `csv_quoting_follows_docstring` | false | to_csv_row returned 'Desk, large "oak",10.00,2' |
| `rule_type_hints` | false | RULE: every public function (name not starting with '_') in the package has type annotations on all parameters and on the return value. |
| `rule_regression_tests` | false | RULE: add tests/test_regressions.py with one test function per bug you fixed (at least 3); the file must pass. |
| `rule_changelog` | false | RULE: record each fix in CHANGELOG.md under the heading '## Unreleased' as a bullet '- fix(&lt;function name&gt;): &lt;short description&gt;' (at least 3 bullets). |

### data-learn: 0/8

Nguồn: [run.json](../results/baseline/data-learn/run.json), [trace](../results/baseline/data-learn/trace.md). Detail trích tối đa 160 ký tự; xem bản gốc để đọc đầy đủ.

| Check | Passed (raw) | Detail trích ngắn |
|---|---|---|
| `north_q1_revenue` | false | FileNotFoundError: [Errno 2] No such file or directory: '/tmp/lab-pg4talmd/workspace/answer.json' |
| `north_q1_orders` | false | FileNotFoundError: [Errno 2] No such file or directory: '/tmp/lab-pg4talmd/workspace/answer.json' |
| `top_region` | false | FileNotFoundError: [Errno 2] No such file or directory: '/tmp/lab-pg4talmd/workspace/answer.json' |
| `missing_amount_orders` | false | FileNotFoundError: [Errno 2] No such file or directory: '/tmp/lab-pg4talmd/workspace/answer.json' |
| `duplicate_rows_removed` | false | FileNotFoundError: [Errno 2] No such file or directory: '/tmp/lab-pg4talmd/workspace/answer.json' |
| `rule_money_in_cents` | false | FileNotFoundError: [Errno 2] No such file or directory: '/tmp/lab-pg4talmd/workspace/answer.json' |
| `rule_meta_block` | false | FileNotFoundError: [Errno 2] No such file or directory: '/tmp/lab-pg4talmd/workspace/answer.json' |
| `rule_clean_csv` | false | RULE: write workspace/clean.csv with the header order_id,timestamp_utc,region,amount_cents; one row per distinct order with a known amount; timestamp_utc as YYY |

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
