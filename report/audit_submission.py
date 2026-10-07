"""Audit existing learning evidence and report links offline; never call a model.

Run from the repository root: .venv/bin/python report/audit_submission.py
Fills marked report sections, an evidence index and audit metadata from saved
records, without altering raw results.
This checks reporting integrity, not completion of freeze/evaluation requirements.
"""
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import re
import statistics
import subprocess

from lab.compare import build_table, load_runs


ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def git(*args):
    # Windows checkout uses CRLF; apply the same clean filter in WSL, without
    # changing config or files. Other content differences remain detectable.
    return subprocess.check_output(["git", "-c", "core.autocrlf=true", *args], cwd=ROOT, text=True, encoding="utf-8").strip()


def cell(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def number(value, places=0):
    return f"{value:,.{places}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def fill_recorded_section(path, marker, content):
    text = path.read_text(encoding="utf-8")
    start, end = f"<!-- BEGIN {marker} -->", f"<!-- END {marker} -->"
    assert text.count(start) == text.count(end) == 1, path
    before, remaining = text.split(start)
    _, after = remaining.split(end)
    path.write_text(before + start + "\n" + content + "\n" + end + after, encoding="utf-8")


def main():
    os.chdir(ROOT)
    report = (ROOT / "report/REPORT.md").read_text(encoding="utf-8")
    runs = []
    for path in sorted((ROOT / "results").rglob("run.json")):
        # Do not inspect evaluation contents before freeze.
        if any(part.endswith("-eval") for part in path.parts):
            continue
        run = read_json(path)
        assert run["role"] == "learn" and run["task"].endswith("-learn"), path
        assert path.with_name("trace.md").is_file(), path
        assert path.with_name("configuration.json").is_file() or (
            path.parents[3] / "configuration.json"
        ).is_file(), path
        runs.append((path, run))
    assert len(runs) == 13, "Report needs updating if new runs have been added"
    tokens = sum(run["tokens"]["total"] for _, run in runs)
    seconds = round(sum(run["seconds"] for _, run in runs), 1)
    errored = sum(bool(run.get("error")) for _, run in runs)
    assert (tokens, seconds, errored) == (288649, 1929.6, 13)
    assert "288.649" in report and "1.929,6" in report
    debug = read_json(ROOT / "report/performance/learning-debug.json")
    assert {r["path"] for r in debug["runs"]} == {p.relative_to(ROOT).as_posix() for p, _ in runs}
    for path, run in runs:
        saved = next(r for r in debug["runs"] if r["path"] == path.relative_to(ROOT).as_posix())
        assert saved["tokens"] == run["tokens"] and saved["seconds"] == run["seconds"]
    table = build_table(load_runs(ROOT / "results"))
    assert table == (ROOT / "report/table.md").read_text(encoding="utf-8").strip()
    assert table in report

    coverage_record = read_json(ROOT / "report/performance/coverage.json")
    coverage = coverage_record["totals"]
    assert (coverage["covered_lines"], coverage["num_statements"], coverage["missing_lines"]) == (423, 467, 44)
    assert math.isclose(coverage["percent_covered"], 100 * 423 / 467)
    verification = (ROOT / "report/performance/verification.log").read_text(encoding="utf-8")
    assert "32 passed in 65.90s" in verification
    assert len(re.findall(r"^PASS ", verification, flags=re.M)) == 32
    controls = (ROOT / "report/performance/benchmark-controls.log").read_text(encoding="utf-8")
    assert len(re.findall(r"^PASS benchmark control:", controls, flags=re.M)) == 3
    offline_path = ROOT / "report/performance/offline-20261006T151924755263Z/summary.json"
    offline = read_json(offline_path)
    assert offline["api_calls"] == 0 and offline["worker_utilization"] is None
    for name, case in offline["cases"].items():
        assert len(case["samples"]) == 3 and all(s["success"] for s in case["samples"])
        for sample in case["samples"]:
            matches = list(offline_path.parent.glob(f"{name}/iteration-{sample['iteration']}/*/*/run.json"))
            assert len(matches) == 1
            raw = read_json(matches[0])
            assert raw["score"] == sample["score"] == 1.0 and not raw["error"]
            assert raw["tokens"]["total"] == 0 and matches[0].with_name("trace.md").is_file()
        assert math.isclose(case["metrics"]["p50"], statistics.median(s["seconds"] for s in case["samples"]))
    stress = offline["stress"]
    assert len(stress["samples"]) == 10 and all(s["success"] for s in stress["samples"])
    for sample in stress["samples"]:
        assert read_json(offline_path.parent / f"stress/request-{sample['request_id']}.json") == sample
    assert offline["profile_sample"]["success"]

    groups = []
    run_summary = ["| Tác vụ | Lượt có lỗi / đã chạy | Input token | Output token | Tổng token | Tổng giây | Tool call chính |", "|---|---:|---:|---:|---:|---:|---:|"]
    for task in sorted({run["task"] for _, run in runs}):
        rs = [run for _, run in runs if run["task"] == task]
        group = {"task": task, "runs": len(rs), "errored": sum(bool(r.get("error")) for r in rs), "input": sum(r["tokens"]["input"] for r in rs), "output": sum(r["tokens"]["output"] for r in rs), "total": sum(r["tokens"]["total"] for r in rs), "seconds": round(sum(r["seconds"] for r in rs), 1), "main_tool_calls": sum(r["tool_calls"] for r in rs), "subagent_calls": sum(r["subagent_calls"] for r in rs), "skills_read": sum(r["skills_read"] for r in rs)}
        groups.append(group)
        values = [task, f"{group['errored']}/{group['runs']}", *[number(group[key]) for key in ("input", "output", "total")], number(group["seconds"], 1), group["main_tool_calls"]]
        run_summary.append("| " + " | ".join(map(str, values)) + " |")
    assert sum(g["total"] for g in groups) == tokens
    assert all(g["subagent_calls"] == g["skills_read"] == 0 for g in groups)
    run_summary.append(f"| **Tổng** | **{errored}/{len(runs)}** | **{number(sum(g['input'] for g in groups))}** | **{number(sum(g['output'] for g in groups))}** | **{number(tokens)}** | **{number(seconds, 1)}** | **{sum(g['main_tool_calls'] for g in groups)}** |")
    categories = ["| Nhóm lỗi thực thi | Số lượt | Tỷ lệ trong 13 lượt |", "|---|---:|---:|"]
    assert sum(debug["categories"].values()) == len(runs)
    for name, count in debug["categories"].items():
        categories.append(f"| {name} | {count} | {count / len(runs) * 100:.2f}% |")
    recorded_summary = "\n".join(run_summary + [""] + categories)
    fill_recorded_section(ROOT / "report/REPORT.md", "REAL-RUN-SUMMARY", recorded_summary)

    details = ["### Suite và các nhóm kiểm chứng", "", "| Bộ kiểm chứng | Đạt | Nguồn |", "|---|---:|---|"]
    for filename, count in (("test_01_provided.py", 15), ("test_02_agent.py", 9), ("test_03_runner.py", 6), ("test_04_curator.py", 2)):
        assert f"tests/{filename} " + "." * count in verification
        details.append(f"| `{filename}` | {count}/{count} | [verification.log](verification.log) |")
    details += ["| Worker/giao tiếp bổ sung | 14/14 nhóm | [verification.log](verification.log) |", "| Tools/hợp tác bổ sung | 14/14 nhóm | [verification.log](verification.log) |", "| Curator bổ sung | 4/4 nhóm | [verification.log](verification.log) |", "| Driver benchmark bổ sung | 3/3 nhóm | [benchmark-controls.log](benchmark-controls.log) |", "", "Tổng suite gốc: 32 test đạt; kiểm chứng bổ sung: 35 nhóm đạt. Các nhóm bổ sung là ca chạy script, không đổi tên thành 35 test pytest. Suite model kịch bản không chứng minh chất lượng Groq.", "", "### Statement coverage từng module", "", "| Module | Statement đã đo / tổng | Coverage | Chưa đo |", "|---|---:|---:|---:|"]
    for filename, record in sorted(coverage_record["files"].items()):
        summary = record["summary"]
        if summary["num_statements"]:
            details.append(f"| `{Path(filename).name}` | {summary['covered_lines']}/{summary['num_statements']} | {summary['percent_covered']:.2f}% | {summary['missing_lines']} |")
    details += ["| **Toàn bộ src/lab** | **423/467** | **90,58%** | **44** |", "", "Nguồn [coverage.json](coverage.json); `__init__.py` có 0 statement nên không tính là module có code được kiểm chứng. Không đo branch coverage.", "", "### Latency và tải đã thực thi", "", "| Fixture | Mẫu đạt / tổng | Min (s) | Max (s) | Avg (s) | P50 (s) | P99 mẫu (s) |", "|---|---:|---:|---:|---:|---:|---:|"]
    for name, case in [*offline["cases"].items(), ("complex, 10 graph đồng thời", offline["stress"])]:
        metrics = case["metrics"]
        details.append(f"| {name} | {metrics['successes']}/{metrics['requests']} | " + " | ".join(f"{metrics[key]:.3f}" for key in ("min", "max", "avg", "p50", "p99_nearest_rank")) + " |")
    metrics = offline["stress"]["metrics"]
    details += ["", f"Burst 10 graph hoàn tất trong {metrics['elapsed_seconds']:.3f}s, tốc độ quy đổi {metrics['successful_requests_per_minute']:.2f} yêu cầu/phút. Không phải throughput duy trì hoặc throughput API; RAM/CPU và worker utilization chưa đo. P99 nearest rank với N=3/10 là max mẫu. Nguồn: [summary](offline-20261006T151924755263Z/summary.json), gồm raw record và ca profiling riêng.", "", "Fixture dùng model kịch bản, API call/token bằng 0; file/shell/SQLite/checker chạy thật. 13 lượt Groq có lỗi được liệt kê riêng trong [RESULTS_INDEX](../RESULTS_INDEX.md)."]
    fill_recorded_section(ROOT / "report/performance/test-results.md", "RECORDED-TEST-RESULTS", "\n".join(details))

    protected = ["tests", "tasks", "scripts", *[f"src/lab/{name}.py" for name in ("model", "tasks", "grading", "testing", "compare")]]
    assert not git("diff", "--name-only", "ad29c55", "--", *protected)
    preserved = {
        "agent": ["PATHS_NOTE", "BASE_PROMPT", "SKILLS_NOTE", "SUBAGENTS_NOTE"],
        "runner": ["CONDITIONS", "render_trace", "main"],
        "curator": ["SAFE_NAME", "validate_skill", "parse_skill_blocks"],
    }
    for module, names in preserved.items():
        path = f"src/lab/{module}.py"
        original = ast.parse(git("show", f"ad29c55:{path}"))
        current = ast.parse((ROOT / path).read_text(encoding="utf-8"))
        def selected(tree):
            return [ast.dump(n) for n in tree.body if getattr(n, "name", None) in names or (
                isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in n.targets)
            )]
        assert selected(original) == selected(current), path
    assert not git("ls-files", "--", ".env")
    assert ".env" in git("check-ignore", ".env")
    assert not list((ROOT / "skills/auto").rglob("SKILL.md"))
    assert "freeze" not in git("tag", "--list").splitlines()
    secret_pattern = re.compile(r"gsk_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{25,}|Bearer\s+[A-Za-z0-9_-]{20,}")
    scanned = 0
    for folder in ("src/lab", "report", "results", "skills/auto"):
        for path in (ROOT / folder).rglob("*"):
            if path.suffix not in {".py", ".md", ".json", ".log", ".txt"} or any(p.endswith("-eval") for p in path.parts):
                continue
            assert not secret_pattern.search(path.read_text(encoding="utf-8")), f"Credential pattern detected in {path.relative_to(ROOT)}"
            scanned += 1

    lines = ["# Danh mục kết quả đã thực thi", "", "Sinh từ các bản ghi hiện có bằng `report/audit_submission.py`; không gọi API, không sửa raw record.", "", "## Lượt Groq thật", "", "Cả 13 lượt dưới đây có lỗi thực thi. Điểm raw không chứng minh chất lượng model; không có bản ghi thay thế cho lượt chưa chạy.", "", "| Run / trace | Tác vụ | Điểm raw | Token | Giây | Loại lỗi |", "|---|---|---:|---:|---:|---|"]
    hashes = {}
    for path, run in runs:
        rel = path.relative_to(ROOT).as_posix()
        error_type = str(run["error"]).split(":", 1)[0].replace("|", "/")
        lines.append(f"| [{path.parent.relative_to(ROOT / 'results').as_posix()}](../{rel}) · [trace](../{path.with_name('trace.md').relative_to(ROOT).as_posix()}) | {run['task']} | {run['passed']}/{run['total']} | {run['tokens']['total']:,} | {run['seconds']:.1f} | {error_type} |")
        for raw in (path, path.with_name("trace.md")):
            hashes[raw.relative_to(ROOT).as_posix()] = hashlib.sha256(raw.read_bytes()).hexdigest()
    lines += [f"| **Tổng: {len(runs)} lượt** | | | **{tokens:,}** | **{seconds:.1f}** | **{errored} có lỗi** |", "", "## Usage theo tác vụ và nhóm lỗi thực thi", "", "Cộng cả các lượt chẩn đoán khác cấu hình để kiểm toán usage; không dùng làm mean score của điều kiện.", "", recorded_summary, "", "## Check raw của hai baseline chính", "", "Check dưới đây được chấm sau khi lượt đã dừng ở quota/guardrail. Không phân loại chúng thành lỗi chất lượng A–G; `tests_not_modified=false` là check trong workspace tác vụ, không phải bằng chứng thư mục tests của repo đã bị sửa. Audit Git xác nhận các tệp có sẵn nguyên vẹn."]
    for task in ("code-learn", "data-learn"):
        raw_path = ROOT / "results/baseline" / task / "run.json"
        raw = read_json(raw_path)
        lines += ["", f"### {task}: {raw['passed']}/{raw['total']}", "", f"Nguồn: [run.json](../results/baseline/{task}/run.json), [trace](../results/baseline/{task}/trace.md). Detail trích tối đa 160 ký tự; xem bản gốc để đọc đầy đủ.", "", "| Check | Passed (raw) | Detail trích ngắn |", "|---|---|---|"]
        for check in raw["checks"]:
            lines.append(f"| `{cell(check['name'])}` | {str(check['passed']).lower()} | {cell(check['detail'][:160])} |")
    lines += ["", "## Kiểm chứng và đo ngoại tuyến", "", "| Kết quả | Bằng chứng |", "|---|---|", "| Suite gốc 32 đạt; curator/worker/tools thêm 32 nhóm đạt | [verification.log](performance/verification.log), [lượt test trước đó](performance/test-results.md) |", "| Driver benchmark thêm 3 nhóm đạt | [benchmark-controls.log](performance/benchmark-controls.log) |", "| Statement coverage 423/467 = 90,58%; thiếu 44 dòng | [coverage.json](performance/coverage.json), [metadata](performance/coverage-summary.json) |", "| Simple/code/complex: 3 lần mỗi nhóm, 9/9 đạt | [summary và đường dẫn raw](performance/offline-20261006T151924755263Z/summary.json) |", "| Tải 10 graph độc lập: 10/10 đạt; không gọi API | [summary stress](performance/offline-20261006T151924755263Z/summary.json) |", "| Ca complex profiling đạt; 352.503 call trong 0,511s trên main thread | [profile.txt](performance/offline-20261006T151924755263Z/profile.txt) |", "| So sánh tạm: chỉ hai baseline học | [table.md](table.md) |", "", "Scripted model quyết định đường gọi; file/shell/SQLite/checker thực thi thật. Không dùng điểm fixture làm điểm Groq. Thử kết nối model riêng trả OK dùng 101 token, đã ghi ở phụ lục REPORT; không nằm trong 13 lượt tác vụ.", "", "## Tính toàn vẹn", "", "[submission-audit.json](performance/submission-audit.json) giữ SHA-256 của từng run/trace, kiểm tra bảng so sánh, coverage, liên kết và các phần có sẵn so với commit gốc. Audit không thay thế pytest, không chứng nhận freeze và không tự nộp bài.", ""]
    (ROOT / "report/RESULTS_INDEX.md").write_text("\n".join(lines), encoding="utf-8")
    audit = {"kind": "offline-existing-evidence-audit", "source_revision": git("rev-parse", "HEAD"), "api_calls": 0, "real_learning_runs": len(runs), "errored_runs": errored, "recorded_tokens": tokens, "recorded_seconds": seconds, "original_suite_passes": 32, "additional_verification_groups": 35, "offline_repeated_requests": 9, "offline_concurrent_requests": 10, "coverage_covered_statements": 423, "coverage_total_statements": 467, "protected_files_unchanged": True, "protected_ast_unchanged": True, "env_untracked_and_ignored": True, "credential_pattern_scanned_files": scanned, "freeze_exists": False, "raw_sha256": hashes}
    audit_path = ROOT / "report/performance/submission-audit.json"
    audit["real_runs_by_task"] = groups
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for filename in ("REPORT.md", "SUBMISSION_CHECKLIST.md", "RESULTS_INDEX.md", "performance/test-results.md"):
        path = ROOT / "report" / filename
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if target.startswith(("https://", "http://", "#")):
                continue
            assert (path.parent / target.split("#", 1)[0]).exists(), f"Broken link in {filename}: {target}"
    print(f"PASS audit: {len(runs)} real learning records, {tokens} recorded tokens, {seconds:.1f}s; table/coverage/raw hashes/protected files/local links verified; API calls=0")


if __name__ == "__main__":
    main()
