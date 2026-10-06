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
