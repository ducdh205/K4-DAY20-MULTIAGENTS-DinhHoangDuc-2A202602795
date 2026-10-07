"""Audit existing learning evidence and report links offline; never call a model.

Run from the repository root: .venv/bin/python report/audit_submission.py
Writes an evidence index and audit metadata, without altering raw results.
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

    coverage = read_json(ROOT / "report/performance/coverage.json")["totals"]
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
    lines += [f"| **Tổng: {len(runs)} lượt** | | | **{tokens:,}** | **{seconds:.1f}** | **{errored} có lỗi** |", "", "## Kiểm chứng và đo ngoại tuyến", "", "| Kết quả | Bằng chứng |", "|---|---|", "| Suite gốc 32 đạt; curator/worker/tools thêm 32 nhóm đạt | [verification.log](performance/verification.log), [lượt test trước đó](performance/test-results.md) |", "| Driver benchmark thêm 3 nhóm đạt | [benchmark-controls.log](performance/benchmark-controls.log) |", "| Statement coverage 423/467 = 90,58%; thiếu 44 dòng | [coverage.json](performance/coverage.json), [metadata](performance/coverage-summary.json) |", "| Simple/code/complex: 3 lần mỗi nhóm, 9/9 đạt | [summary và đường dẫn raw](performance/offline-20261006T151924755263Z/summary.json) |", "| Tải 10 graph độc lập: 10/10 đạt; không gọi API | [summary stress](performance/offline-20261006T151924755263Z/summary.json) |", "| Ca complex profiling đạt; 352.503 call trong 0,511s trên main thread | [profile.txt](performance/offline-20261006T151924755263Z/profile.txt) |", "| So sánh tạm: chỉ hai baseline học | [table.md](table.md) |", "", "Scripted model quyết định đường gọi; file/shell/SQLite/checker thực thi thật. Không dùng điểm fixture làm điểm Groq. Thử kết nối model riêng trả OK dùng 101 token, đã ghi ở phụ lục REPORT; không nằm trong 13 lượt tác vụ.", "", "## Tính toàn vẹn", "", "[submission-audit.json](performance/submission-audit.json) giữ SHA-256 của từng run/trace, kiểm tra bảng so sánh, coverage, liên kết và các phần có sẵn so với commit gốc. Audit không thay thế pytest, không chứng nhận freeze và không tự nộp bài.", ""]
    (ROOT / "report/RESULTS_INDEX.md").write_text("\n".join(lines), encoding="utf-8")
    audit = {"kind": "offline-existing-evidence-audit", "source_revision": git("rev-parse", "HEAD"), "api_calls": 0, "real_learning_runs": len(runs), "errored_runs": errored, "recorded_tokens": tokens, "recorded_seconds": seconds, "original_suite_passes": 32, "additional_verification_groups": 35, "offline_repeated_requests": 9, "offline_concurrent_requests": 10, "coverage_covered_statements": 423, "coverage_total_statements": 467, "protected_files_unchanged": True, "protected_ast_unchanged": True, "env_untracked_and_ignored": True, "credential_pattern_scanned_files": scanned, "freeze_exists": False, "raw_sha256": hashes}
    audit_path = ROOT / "report/performance/submission-audit.json"
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for filename in ("REPORT.md", "SUBMISSION_CHECKLIST.md", "RESULTS_INDEX.md"):
        path = ROOT / "report" / filename
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if target.startswith(("https://", "http://", "#")):
                continue
            assert (path.parent / target.split("#", 1)[0]).exists(), f"Broken link in {filename}: {target}"
    print(f"PASS audit: {len(runs)} real learning records, {tokens} recorded tokens, {seconds:.1f}s; table/coverage/raw hashes/protected files/local links verified; API calls=0")


if __name__ == "__main__":
    main()
