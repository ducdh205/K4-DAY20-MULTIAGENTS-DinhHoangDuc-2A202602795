"""Offline integration checks: scripted model decisions, real sandbox file/shell tools.

No provider calls, benchmark records, or changes to the provided tests/tasks.
Run with the WSL virtualenv: python report/verify_worker_communication.py
"""
import asyncio
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
from typing import Any
from datetime import datetime

from langchain_core.exceptions import ModelRateLimitError
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from lab.agent import build_agent
from lab.runner import run_task
from lab.testing import ScriptedChatModel


class CommunicationModel(ScriptedChatModel):
    barrier: Any = None
    observed: list = []
    failure: str = ""

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        system = str(messages[0].content)
        role = next((name for prefix, name in [
            ("You investigate", "explorer"),
            ("You implement", "implementer"),
            ("You independently review", "reviewer"),
        ] if system.startswith(prefix)), "coordinator")
        self.observed.append((role, "\n".join(str(m.content) for m in messages if m.type == "human")))
        outputs = [m for m in messages if isinstance(m, ToolMessage)]

        def call(name, args, identity):
            return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": identity}])

        if role == "coordinator":
            if not outputs:
                reply = AIMessage(content="", tool_calls=[
                    {"name": "task", "args": {"subagent_type": "explorer", "description": "Read workspace/sample.csv using Python; report the row count. Do not change files."}, "id": "delegate-data"},
                    {"name": "task", "args": {"subagent_type": "implementer", "description": "Create workspace/generated.txt containing worker output followed by a newline. Validate the file using Python."}, "id": "delegate-code"},
                ])
            elif any(m.status == "error" or json.loads(m.content).get("status") == "error" for m in outputs):
                reply = AIMessage(content="Worker failure detected; remaining worker result preserved")
            elif not any(m.tool_call_id == "delegate-review" for m in outputs):
                reply = call("task", {"subagent_type": "reviewer", "description": "Read workspace/generated.txt and verify it contains worker output. Do not change files."}, "delegate-review")
            else:
                reply = AIMessage(content="Verified workspace/generated.txt")
        else:
            if not outputs and role in {"explorer", "implementer"}:
                self.barrier.wait(timeout=10)  # Both workers must start concurrently.
            if role == "explorer" and not outputs and self.failure == "timeout":
                raise TimeoutError("PRIVATE-EXCEPTION-MARKER")
            if role == "explorer" and not outputs and self.failure == "runtime":
                raise RuntimeError("upstream unavailable")
            if role == "explorer" and not outputs and self.failure == "provider":
                raise ModelRateLimitError("Offline provider quota error")
            if role == "explorer" and not outputs and self.failure == "reported":
                return ChatResult(generations=[ChatGeneration(message=AIMessage(content=json.dumps({
                    "status": "error", "result": None, "files_changed": [], "checks": [],
                    "errors": ["Verification scenario: worker reported an unresolved check"],
                })))])
            if role == "explorer" and not outputs:
                reply = call("execute", {"command": "python -c \"import csv,json; print(json.dumps({'rows': len(list(csv.DictReader(open('workspace/sample.csv'))))}))\""}, "count-rows")
            elif role == "implementer" and not outputs:
                reply = call("write_file", {"file_path": "workspace/generated.txt", "content": "worker output\n"}, "write-output")
            elif role == "implementer" and len(outputs) == 1:
                reply = call("execute", {"command": "python -c \"from pathlib import Path; assert Path('workspace/generated.txt').read_text() == 'worker output\\n'; print('VERIFIED')\""}, "validate-output")
            elif role == "reviewer" and not outputs:
                reply = call("read_file", {"file_path": "workspace/generated.txt"}, "read-output")
            else:
                evidence = str(outputs[-1].content)
                marker = {"explorer": '"rows": 2', "implementer": "VERIFIED", "reviewer": "worker output"}[role]
                passed = marker in evidence
                reply = AIMessage(content=json.dumps({
                    "status": "success" if passed else "error", "result": evidence,
                    "files_changed": ["workspace/generated.txt"] if role == "implementer" else [],
                    "checks": [{"check": role, "passed": passed, "evidence": evidence}],
                    "errors": [] if passed else ["Expected validation marker missing"],
                }))
        return ChatResult(generations=[ChatGeneration(message=reply)])


def verify_flow(use_async, failure=""):
    with TemporaryDirectory(prefix="worker-check-") as folder:
        root = Path(folder)
        (root / "workspace").mkdir()
        (root / "workspace/sample.csv").write_text("name,value\na,2\nb,3\n")
        model = CommunicationModel(barrier=Barrier(2), failure=failure)
        graph = build_agent(root, mode="subagents", model=model)
        state = {"messages": [{"role": "user", "content": "PRIVATE-MAIN-MARKER: delegate data, code, then review."}]}
        result = asyncio.run(graph.ainvoke(state, config={"recursion_limit": 30})) if use_async else graph.invoke(state, config={"recursion_limit": 30})
        reports = {m.tool_call_id: json.loads(m.content) for m in result["messages"] if isinstance(m, ToolMessage)}
        if failure:
            assert set(reports) == {"delegate-data", "delegate-code"}
            assert reports["delegate-data"]["status"] == "error"
            assert reports["delegate-code"]["status"] == "success"
            assert "PRIVATE-EXCEPTION-MARKER" not in str(result["messages"])
            data_message = next(m for m in result["messages"] if isinstance(m, ToolMessage) and m.tool_call_id == "delegate-data")
            assert data_message.status == ("error" if failure == "timeout" else "success")
        else:
            assert set(reports) == {"delegate-data", "delegate-code", "delegate-review"}
            assert all(r["status"] == "success" for r in reports.values())
        assert (root / "workspace/generated.txt").read_text() == "worker output\n"
        assert all("PRIVATE-MAIN-MARKER" not in prompt for role, prompt in model.observed if role != "coordinator")
        assert {role for role, prompt in model.observed} == ({"coordinator", "explorer", "implementer"} if failure else {"coordinator", "explorer", "implementer", "reviewer"})
    print(f"PASS {'async' if use_async else 'sync'} {failure or 'success'}: correlated replies, real tools, isolated context")


class RecordModel(ScriptedChatModel):
    failure: str = "timeout"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        if str(messages[0].content).startswith("You investigate"):
            if self.failure == "timeout":
                raise TimeoutError("PRIVATE-EXCEPTION-MARKER")
            if self.failure == "provider":
                raise ModelRateLimitError("Offline provider quota error")
            reply = AIMessage(content=json.dumps({"status": "success" if self.failure == "success" else "error", "errors": [] if self.failure == "success" else ["Unresolved check"]}))
        elif not any(isinstance(m, ToolMessage) for m in messages):
            reply = AIMessage(content="", tool_calls=[{"name": "task", "args": {"subagent_type": "explorer", "description": "Offline verification of result recording; return your status."}, "id": "record-worker-error"}])
        else:
            reply = AIMessage(content="Worker returned its status")
        return ChatResult(generations=[ChatGeneration(message=reply)])


def verify_error_record(failure):
    with TemporaryDirectory(prefix="worker-record-check-") as folder:
        record = run_task("data-learn", "subagents", results_dir=folder, model=RecordModel(failure=failure))
        if failure in {"timeout", "reported"}:
            assert record["error"] and "explorer" in record["error"]
            assert record["final_message"] == ""
            assert len(record["worker_errors"]) == 1
            assert record["worker_errors"][0]["tool_call_id"] == "record-worker-error"
            assert record["worker_errors"][0]["report"]["status"] == "error"
        else:
            assert record["worker_errors"] == []
            assert (record["error"] is None) == (failure == "success")
            if failure == "provider":
                assert "ModelRateLimitError" in record["error"]
        communication = record["communications"]
        assert len(communication) == (1 if failure == "provider" else 2)
        assert communication[0]["type"] == "task"
        assert communication[0]["from"] == "coordinator" and communication[0]["to"] == "explorer"
        assert all(m["id"] == "record-worker-error" and datetime.fromisoformat(m["timestamp"]).utcoffset().total_seconds() == 0 for m in communication)
        if failure != "provider":
            assert communication[1]["type"] == "result"
            assert communication[1]["from"] == "explorer" and communication[1]["to"] == "coordinator"
        saved = json.loads((Path(folder) / "subagents/data-learn/run.json").read_text())
        assert saved["worker_errors"] == record["worker_errors"]
        assert saved["communications"] == communication
        assert "PRIVATE-EXCEPTION-MARKER" not in json.dumps(saved)
    print(f"PASS runner {failure}: correlated communication log and honest error state saved in temporary directory")


if __name__ == "__main__":
    # Make the verification independent of optional provider-budget environment settings.
    for variable in ("LAB_MAX_INPUT_TOKENS", "LAB_MAX_OUTPUT_TOKENS"):
        os.environ.pop(variable, None)
    verify_flow(False)
    verify_flow(True)
    verify_flow(False, "timeout")
    verify_flow(True, "timeout")
    verify_flow(False, "reported")
    verify_flow(True, "reported")
    for failure in ("runtime", "provider"):
        for use_async in (False, True):
            try:
                verify_flow(use_async, failure)
            except (RuntimeError, ModelRateLimitError) as exc:
                assert isinstance(exc, ModelRateLimitError if failure == "provider" else RuntimeError)
                print(f"PASS {'async' if use_async else 'sync'} {failure}: error propagates")
            else:
                raise AssertionError("Unexpected/provider error was masked")
    for failure in ("timeout", "reported", "success", "provider"):
        verify_error_record(failure)
