"""Offline tools checks with real local execution and synthetic temporary fixtures.

No API calls, provided task/test changes, or benchmark results.
Run in WSL: .venv/bin/python report/verify_tool_integration.py
"""
import asyncio
import json
import os
import shlex
import sqlite3
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from lab.agent import build_agent, make_backend
from lab.grading import grade
from lab.runner import run_task
from lab.tasks import Task
from lab.testing import ScriptedChatModel


ANALYSIS = '''import csv, json, sqlite3
from decimal import Decimal, InvalidOperation
from pathlib import Path

def analyze():
    amounts, rejected = [], 0
    with open("workspace/sales.csv", encoding="utf-8", newline="") as source:
        rows = csv.DictReader(source)
        if rows.fieldnames != ["id", "amount"]:
            raise ValueError("Expected CSV columns id,amount")
        for row in rows:
            try:
                amount = Decimal(row["amount"])
                if not amount.is_finite() or amount * 100 != (amount * 100).to_integral_value():
                    raise ValueError("Amount must be finite cents")
                amounts.append(int(amount * 100))
            except (InvalidOperation, ValueError):
                rejected += 1
    database = sqlite3.connect(Path("workspace/sales.db").resolve().as_uri() + "?mode=ro", uri=True)
    try:
        sql_total = database.execute("SELECT SUM(cents) FROM sales WHERE year = ?", (2026,)).fetchone()[0]
        try:
            database.execute("DELETE FROM sales")
        except sqlite3.OperationalError:
            readonly = True
        else:
            raise AssertionError("Read-only database accepted a write")
    finally:
        database.close()
    if sql_total != sum(amounts):
        raise ValueError("CSV and database totals differ")
    return {"total_cents": sum(amounts), "valid_rows": len(amounts), "rejected_rows": rejected,
            "sql_total_cents": sql_total, "readonly": readonly}

if __name__ == "__main__":
    print(json.dumps(analyze()))
'''

REPORT_SCRIPT = '''import json
from pathlib import Path
from analysis import analyze
label = "DRAFT"
report = analyze()
Path("workspace/answer.json").write_text(json.dumps(report), encoding="utf-8")
Path("workspace/summary.svg").write_text(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="300" height="60"><title>{label}</title>'
    f'<rect width="{report["total_cents"] / 10}" height="20" /></svg>', encoding="utf-8")
print(json.dumps(report))
'''

CHECKER = '''import argparse, json
from pathlib import Path
from xml.etree import ElementTree as ET
parser = argparse.ArgumentParser()
parser.add_argument("--workspace", default="workspace")
root = Path(parser.parse_args().workspace)
try:
    answer = json.loads((root / "answer.json").read_text())
except (OSError, ValueError):
    answer = {}
try:
    image = ET.parse(root / "summary.svg").getroot()
    chart_ok = (image.find("{http://www.w3.org/2000/svg}title").text == "Sales summary"
                and float(image.find("{http://www.w3.org/2000/svg}rect").get("width")) == 137.5)
except (OSError, ET.ParseError, AttributeError, TypeError, ValueError):
    chart_ok = False
checks = [
    {"name": "totals", "passed": answer.get("total_cents") == 1375 and answer.get("sql_total_cents") == 1375},
    {"name": "rows_and_readonly", "passed": answer.get("valid_rows") == 3 and answer.get("rejected_rows") == 2 and answer.get("readonly") is True},
    {"name": "chart", "passed": chart_ok},
]
for check in checks:
    check["detail"] = "Synthetic fixture requirement not met" if not check["passed"] else ""
passed = sum(check["passed"] for check in checks)
print(json.dumps({"score": passed / len(checks), "passed": passed, "total": len(checks), "checks": checks}))
'''


def make_fixture(root):
    workspace = root / "workspace"
    workspace.mkdir()
    (workspace / "sales.csv").write_text("id,amount\n1,10.50\n2,5.25\n3,-2.00\n4,\n5,bad\n", encoding="utf-8")
    with sqlite3.connect(workspace / "sales.db") as database:
        database.execute("CREATE TABLE sales (id INTEGER, cents INTEGER, year INTEGER)")
        database.executemany("INSERT INTO sales VALUES (?, ?, ?)", [(1, 1050, 2026), (2, 525, 2026), (3, -200, 2026)])
    (workspace / "analysis.py").write_text(ANALYSIS, encoding="utf-8")
    (root / "check.py").write_text(CHECKER, encoding="utf-8")
    (workspace / "check_outputs.py").write_text(CHECKER, encoding="utf-8")
    return Task("tools-fixture-learn", "tools-fixture", "learn", "Synthetic CSV/SQLite tool collaboration fixture.", root)


def python_command(code):
    return "exec python -c " + shlex.quote(code)


def verify_backend():
    with TemporaryDirectory(prefix="tool-check-") as folder:
        parent = Path(folder)
        root = parent / "sandbox"
        root.mkdir()
        outside = parent / "outside.txt"
        outside.write_text("SYNTHETIC-OUTSIDE-FIXTURE", encoding="utf-8")
        with patch.dict(os.environ, {"LAB_API_KEY": "SYNTHETIC-ENV-MARKER"}):
            backend = make_backend(root)
            response = backend.execute(python_command(
                "import os; assert 'LAB_API_KEY' not in os.environ; print('ENV_OK')"
            ))
        assert response.exit_code == 0 and "ENV_OK" in response.output
        print("PASS backend environment: parent credential marker not inherited")

        assert not backend.write("workspace/message.txt", "Xin chào\n").error
        assert not backend.edit("workspace/message.txt", "Xin chào", "Đã kiểm tra").error
        assert "Đã kiểm tra" in backend.read("workspace/message.txt").file_data["content"]
        response = backend.execute(python_command(
            "from pathlib import Path; assert Path('workspace/message.txt').read_text() == 'Đã kiểm tra\\n'"
        ))
        assert response.exit_code == 0
        print("PASS backend files: UTF-8 create/edit/read and shell use the same path")

        assert backend.read("workspace/missing.txt").error
        assert backend.edit("workspace/message.txt", "absent", "replacement").error
        assert backend.execute("").exit_code != 0
        print("PASS backend invalid input: missing file, edit mismatch, empty command")

        for invalid in ("../outside.txt", "workspace/../../outside.txt"):
            try:
                backend.write(invalid, "should never be written")
            except ValueError:
                pass
            else:
                raise AssertionError("File traversal was accepted")
        (root / "escape").symlink_to(parent, target_is_directory=True)
        try:
            backend.write("escape/outside.txt", "should never be written")
        except ValueError:
            pass
        else:
            raise AssertionError("Symlink escape was accepted")
        assert outside.read_text() == "SYNTHETIC-OUTSIDE-FIXTURE"
        print("PASS backend file paths: traversal and symlink escape rejected")

        response = backend.execute(python_command(
            "import sys; print('STDOUT_MARKER'); print('STDERR_MARKER', file=sys.stderr); sys.exit(3)"
        ))
        assert response.exit_code == 3
        assert "STDOUT_MARKER" in response.output and "[stderr] STDERR_MARKER" in response.output
        print("PASS backend failures: stdout/stderr and nonzero exit preserved")

        started = time.perf_counter()
        response = backend.execute(python_command("import time; time.sleep(2)"), timeout=1)
        assert response.exit_code == 124 and "timed out" in response.output
        assert time.perf_counter() - started < 5
        print("PASS backend timeout: real command exceeds 1 second and returns exit 124")

        response = backend.execute(python_command("print('x' * 20000)"))
        assert response.truncated and response.output.count("x") == 10000
        print("PASS backend output: 20,000-character result truncated at 10,000")

        # Demonstrate the precise boundary without touching host secrets/files.
        response = backend.execute("cat " + shlex.quote(str(outside)))
        assert response.exit_code == 0 and "SYNTHETIC-OUTSIDE-FIXTURE" in response.output
        print("PASS backend boundary: shell can read our outside fixture; no OS isolation claimed")


class CollaborationModel(ScriptedChatModel):
    corrupt: bool = False

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        system = str(messages[0].content)
        role = next((name for prefix, name in (
            ("You investigate", "explorer"), ("You implement", "implementer"),
            ("You independently review", "reviewer"),
        ) if system.startswith(prefix)), "coordinator")
        outputs = [message for message in messages if isinstance(message, ToolMessage)]

        def call(name, args):
            return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": f"{role}-{len(outputs)}"}])

        if role == "coordinator" and len(outputs) < 3:
            worker = ("explorer", "implementer", "reviewer")[len(outputs)]
            reply = call("task", {"subagent_type": worker, "description":
                "Synthetic fixture: workspace/sales.csv and sales.db contain three valid sales and two invalid CSV rows. "
                "Use workspace/analysis.py to compute totals in cents and verify the SQLite connection is read-only. "
                "Implementation writes workspace/report.py, answer.json and summary.svg titled Sales summary. "
                "Reviewer runs workspace/check_outputs.py independently. Return actual tool evidence. "
                + ("Previous worker report: " + str(outputs[-1].content) if outputs else "")})
        elif role == "coordinator":
            reply = AIMessage(content="Synthetic collaboration completed; consult independent check results.")
        elif role == "explorer" and not outputs:
            reply = call("execute", {"command": "python workspace/analysis.py"})
        elif role == "implementer" and not outputs:
            script = REPORT_SCRIPT
            if self.corrupt:
                script += '\nreport["total_cents"] = 0\nPath("workspace/answer.json").write_text(json.dumps(report))\n'
            reply = call("write_file", {"file_path": "workspace/report.py", "content": script})
        elif role == "implementer" and len(outputs) == 1:
            reply = call("edit_file", {"file_path": "workspace/report.py", "old_string": 'label = "DRAFT"', "new_string": 'label = "Sales summary"'})
        elif role == "implementer" and len(outputs) == 2:
            reply = call("execute", {"command": "python workspace/report.py"})
        elif role == "reviewer" and not outputs:
            reply = call("execute", {"command": "python workspace/check_outputs.py"})
        else:
            evidence = json.loads(str(outputs[-1].content).splitlines()[0])
            passed = role != "reviewer" or evidence["passed"] == evidence["total"]
            reply = AIMessage(content=json.dumps({
                "status": "success" if passed else "error", "result": evidence,
                "files_changed": ["workspace/report.py", "workspace/answer.json", "workspace/summary.svg"] if role == "implementer" else [],
                "checks": [{"check": role, "passed": passed, "evidence": evidence}],
                "errors": [] if passed else ["Independent artifact check failed"],
            }))
        # Deliberately omit the provided model's synthetic token usage metadata.
        return ChatResult(generations=[ChatGeneration(message=reply)])


def verify_collaboration(use_async, corrupt):
    with TemporaryDirectory(prefix="tool-collaboration-") as folder:
        root = Path(folder)
        task = make_fixture(root)
        graph = build_agent(root, mode="subagents", model=CollaborationModel(corrupt=corrupt))
        state = {"messages": [{"role": "user", "content": task.instruction}]}
        cfg = {"recursion_limit": 40}
        result = asyncio.run(graph.ainvoke(state, cfg)) if use_async else graph.invoke(state, cfg)
        reports = [json.loads(m.content) for m in result["messages"] if isinstance(m, ToolMessage)]
        assert len(reports) == 3
        assert reports[0]["result"]["total_cents"] == 1375 and reports[0]["result"]["readonly"]
        assert reports[-1]["status"] == ("error" if corrupt else "success")
        grading = grade(task, root / "workspace")
        assert grading["passed"] == (2 if corrupt else 3) and grading["total"] == 3
        assert grading["score"] == reports[-1]["result"]["score"]
    print(f"PASS collaboration {'async' if use_async else 'sync'} {'corrupt' if corrupt else 'success'}: real tools; independent checks {grading['passed']}/3")


def verify_runner_tools(corrupt):
    with TemporaryDirectory(prefix="tool-records-") as folder:
        root = Path(folder)
        fixture = root / "fixture"
        fixture.mkdir()
        task = make_fixture(fixture)
        with patch("lab.runner.get_task", return_value=task):
            record = run_task(task.id, "subagents", results_dir=root / "records", model=CollaborationModel(corrupt=corrupt))
        assert record["passed"] == (2 if corrupt else 3) and record["total"] == 3
        assert bool(record["error"]) == corrupt and len(record["worker_errors"]) == int(corrupt)
        assert record["tokens"]["total"] == 0 and record["subagent_calls"] == 3
        assert len(record["communications"]) == 6
        events = record["tool_executions"]
        assert len(events) == 8 and len({event["id"] for event in events}) == 8
        assert sorted(event["name"] for event in events) == ["edit_file", "execute", "execute", "execute", "task", "task", "task", "write_file"]
        assert all(event["status"] == "completed" and event["seconds"] >= 0 and event["parent_id"] for event in events)
        saved = json.loads((root / f"records/subagents/{task.id}/run.json").read_text())
        assert saved["tool_executions"] == events
    print(f"PASS runner tools {'corrupt' if corrupt else 'success'}: 8 correlated tool events incl. worker tools, 6 handoff events, 0 API tokens")


if __name__ == "__main__":
    for variable in ("LAB_MAX_INPUT_TOKENS", "LAB_MAX_OUTPUT_TOKENS"):
        os.environ.pop(variable, None)
    verify_backend()
    for corrupt in (False, True):
        for use_async in (False, True):
            verify_collaboration(use_async, corrupt)
        verify_runner_tools(corrupt)
