# Kết quả kiểm chứng Phần 5

Kết quả dưới đây chép từ output thực tế của lệnh trong WSL, với harness tại commit `9b49902`. Không sửa test gốc.

```text
.venv/bin/python -m pytest -v --durations=10

tests/test_01_provided.py ...............
tests/test_02_agent.py .........
tests/test_03_runner.py ......
tests/test_04_curator.py ..

32 passed in 39.51s
```

Các test chậm nhất được pytest ghi nhận:

| Test | Giây |
|---|---:|
| `test_untouched_workspace_does_not_score_full` | 15,83 |
| `test_validate_skill_accepts_good_and_rejects_bad` | 0,71 |
| `test_make_model_supports_an_openai_compatible_endpoint` | 0,49 |
| `test_file_tools_and_shell_share_relative_paths` | 0,36 |
| `test_curator_writes_only_valid_skills_and_never_leaks` | 0,33 |
| `test_feedback_only_on_failed_checks_of_learning_tasks` | 0,21 |
| `test_modifying_skills_is_flagged` | 0,17 |
| `test_skill_reads_and_subagent_calls_are_counted` | 0,15 |
| `test_run_task_saves_a_complete_record` | 0,15 |
| `test_task_workspace_in_repo_is_never_modified` | 0,15 |

Trước thay đổi, `pytest tests/test_04_curator.py -v` tái hiện 2 failed in 2,60s, đều `NotImplementedError` tại `curate_skills`. Sau triển khai đầu tiên, hai test đạt trong 0,69s. Bốn nhóm kiểm chứng bổ sung trong `report/verify_curator.py` đạt, exit code 0: lọc lỗi hạ tầng; JSON/check sai, trace dài, dữ liệu eval và khối trùng; symlink ra ngoài; giới hạn skill 0/âm. Các skill kiểm thử chỉ ghi trong thư mục tạm và được dọn.

Sau đó cài `coverage==7.16.2` và chạy `report/measure_coverage.py`, đo suite gốc cùng ba script kiểm chứng ngoại tuyến. Output đầy đủ lưu trong [verification.log](verification.log): **32 passed in 65,90s**, 4 nhóm curator, 14 nhóm worker/giao tiếp và 14 nhóm tools/hợp tác đều đạt. [coverage-summary.json](coverage-summary.json) ghi **90,58% statement coverage** của toàn bộ `src/lab`; [coverage.json](coverage.json) giữ số dòng đo thực tế. Đây không phải branch coverage hay bằng chứng chất lượng mô hình.

Các ca tải/đo hiệu suất ngoại tuyến nằm trong `offline-20261006T151924755263Z/`, có raw record và checker thực thi thật. Hai lần chạy pytest phục vụ hai mục đích riêng: lần đầu kiểm chứng sau sửa, lần sau đo coverage và lưu log.

## Chi tiết từ log và JSON đã lưu

Phần dưới được `report/audit_submission.py` điền từ log kiểm chứng, coverage JSON và summary hiệu suất hiện có. Không chạy lại test/model để tạo số liệu này; từng phép đo giữ thời điểm và source revision gốc.

<!-- BEGIN RECORDED-TEST-RESULTS -->
### Suite và các nhóm kiểm chứng

| Bộ kiểm chứng | Đạt | Nguồn |
|---|---:|---|
| `test_01_provided.py` | 15/15 | [verification.log](verification.log) |
| `test_02_agent.py` | 9/9 | [verification.log](verification.log) |
| `test_03_runner.py` | 6/6 | [verification.log](verification.log) |
| `test_04_curator.py` | 2/2 | [verification.log](verification.log) |
| Worker/giao tiếp bổ sung | 14/14 nhóm | [verification.log](verification.log) |
| Tools/hợp tác bổ sung | 14/14 nhóm | [verification.log](verification.log) |
| Curator bổ sung | 4/4 nhóm | [verification.log](verification.log) |
| Driver benchmark bổ sung | 3/3 nhóm | [benchmark-controls.log](benchmark-controls.log) |

Tổng suite gốc: 32 test đạt; kiểm chứng bổ sung: 35 nhóm đạt. Các nhóm bổ sung là ca chạy script, không đổi tên thành 35 test pytest. Suite model kịch bản không chứng minh chất lượng Groq.

### Statement coverage từng module

| Module | Statement đã đo / tổng | Coverage | Chưa đo |
|---|---:|---:|---:|
| `agent.py` | 48/51 | 94.12% | 3 |
| `compare.py` | 38/43 | 88.37% | 5 |
| `curator.py` | 80/90 | 88.89% | 10 |
| `grading.py` | 13/15 | 86.67% | 2 |
| `model.py` | 15/15 | 100.00% | 0 |
| `runner.py` | 136/157 | 86.62% | 21 |
| `subagents.py` | 3/3 | 100.00% | 0 |
| `tasks.py` | 59/60 | 98.33% | 1 |
| `testing.py` | 31/33 | 93.94% | 2 |
| **Toàn bộ src/lab** | **423/467** | **90,58%** | **44** |

Nguồn [coverage.json](coverage.json); `__init__.py` có 0 statement nên không tính là module có code được kiểm chứng. Không đo branch coverage.

### Latency và tải đã thực thi

| Fixture | Mẫu đạt / tổng | Min (s) | Max (s) | Avg (s) | P50 (s) | P99 mẫu (s) |
|---|---:|---:|---:|---:|---:|---:|
| simple | 3/3 | 0.221 | 0.779 | 0.407 | 0.223 | 0.779 |
| code | 3/3 | 0.167 | 0.273 | 0.223 | 0.229 | 0.273 |
| complex | 3/3 | 0.340 | 0.502 | 0.406 | 0.376 | 0.502 |
| complex, 10 graph đồng thời | 10/10 | 1.450 | 2.083 | 1.802 | 1.853 | 2.083 |

Burst 10 graph hoàn tất trong 2.181s, tốc độ quy đổi 275.13 yêu cầu/phút. Không phải throughput duy trì hoặc throughput API; RAM/CPU và worker utilization chưa đo. P99 nearest rank với N=3/10 là max mẫu. Nguồn: [summary](offline-20261006T151924755263Z/summary.json), gồm raw record và ca profiling riêng.

Fixture dùng model kịch bản, API call/token bằng 0; file/shell/SQLite/checker chạy thật. 13 lượt Groq có lỗi được liệt kê riêng trong [RESULTS_INDEX](../RESULTS_INDEX.md).
<!-- END RECORDED-TEST-RESULTS -->
