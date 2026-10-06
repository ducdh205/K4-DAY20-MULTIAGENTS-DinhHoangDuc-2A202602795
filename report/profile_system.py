"""Measure the offline harness with real tools and scripted model routing.

Fixture records live under report/performance, never the official results tree.
Run: python report/profile_system.py --repetitions 3 --concurrency 10
"""
import argparse
import asyncio
import cProfile
import io
import json
import math
import os
import platform
import pstats
import statistics
import subprocess
import time
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from lab.agent import build_agent
from lab.grading import grade
from lab.runner import run_task
from lab.testing import ScriptedChatModel
from verify_tool_integration import CollaborationModel, REPORT_SCRIPT, make_fixture


class OfflineModel(ScriptedChatModel):
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        reply = self.script[min(self.calls, len(self.script) - 1)]
        self.calls += 1
        return ChatResult(generations=[ChatGeneration(message=reply)])


def metrics(samples, elapsed):
    latencies = sorted(sample["seconds"] for sample in samples)
    successes = sum(sample["success"] for sample in samples)
    return {"requests": len(samples), "successes": successes,
            "error_rate": 1 - successes / len(samples), "min": min(latencies),
            "max": max(latencies), "avg": statistics.mean(latencies),
            "p50": statistics.median(latencies),
            "p99_nearest_rank": latencies[math.ceil(.99 * len(latencies)) - 1],
            "elapsed_seconds": elapsed, "successful_requests_per_minute": 60 * successes / elapsed,
            "api_tokens": 0}


def measure_request(case, iteration, destination):
    with TemporaryDirectory(prefix="profile-fixture-") as folder:
        root = Path(folder)
        task = make_fixture(root)
        task = replace(task, instruction=f"Offline fixture: {case}. Create valid answer.json and summary.svg.")
        if case == "complex":
            model, condition = CollaborationModel(), "subagents"
        else:
            def call(name, args, identity):
                return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": identity}])
            script = []
            if case == "simple":
                (root / "workspace/report.py").write_text(REPORT_SCRIPT.replace("DRAFT", "Sales summary"))
            else:
                script.append(call("write_file", {"file_path": "workspace/report.py", "content": REPORT_SCRIPT.replace("DRAFT", "Sales summary")}, "create-report"))
            script.extend([call("execute", {"command": "python workspace/report.py"}, "run-report"), AIMessage(content="Fixture finished")])
            model, condition = OfflineModel(script=script), "baseline"
        started = time.perf_counter()
        with patch("lab.runner.get_task", return_value=task):
            record = run_task(task.id, condition, results_dir=destination / case / f"iteration-{iteration}", model=model)
        sample = {"case": case, "iteration": iteration, "seconds": time.perf_counter() - started,
                  "success": record["error"] is None and record["score"] == 1,
                  "score": record["score"], "error": record["error"],
                  "main_tool_calls": record["tool_calls"], "tool_events": len(record["tool_executions"]),
                  "delegation_seconds": sum(event["seconds"] or 0 for event in record["tool_executions"] if event["name"] == "task")}
        assert record["tokens"]["total"] == 0
        return sample


async def concurrent_request(identity, destination):
    started = time.perf_counter()
    with TemporaryDirectory(prefix=f"stress-{identity}-") as folder:
        root = Path(folder)
        task = make_fixture(root)
        graph = build_agent(root, mode="subagents", model=CollaborationModel())
        result = await asyncio.wait_for(graph.ainvoke(
            {"messages": [{"role": "user", "content": f"Offline independent fixture {identity}"}]},
            config={"recursion_limit": 40}), timeout=120)
        grading = await asyncio.to_thread(grade, task, root / "workspace")
        # Compare saved content across requests as well as each independent checker.
        answer = json.loads((root / "workspace/answer.json").read_text())
        success = grading["score"] == 1 and answer["total_cents"] == 1375
        report = {"case": "complex-concurrent", "request_id": identity,
                  "seconds": time.perf_counter() - started, "success": success,
                  "checks": grading, "answer": answer,
                  "messages": [{"type": m.type, "content": m.content,
                                "tool_call_id": getattr(m, "tool_call_id", None)} for m in result["messages"]]}
        (destination / f"request-{identity}.json").write_text(json.dumps(report, indent=2))
        return report


async def stress(count, destination):
    started = time.perf_counter()
    results = await asyncio.gather(*(concurrent_request(i, destination) for i in range(count)), return_exceptions=True)
    samples = [result if isinstance(result, dict) else {"request_id": i, "seconds": time.perf_counter() - started,
               "success": False, "error": type(result).__name__} for i, result in enumerate(results)]
    return {"samples": samples, "metrics": metrics(samples, time.perf_counter() - started)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--concurrency", type=int, default=10)
    args = parser.parse_args()
    if args.repetitions < 3 or args.concurrency < 1:
        parser.error("at least three repetitions and positive concurrency required")
    for name in ("LAB_MAX_INPUT_TOKENS", "LAB_MAX_OUTPUT_TOKENS"):
        os.environ.pop(name, None)
    destination = Path("report/performance") / datetime.now(timezone.utc).strftime("offline-%Y%m%dT%H%M%S%fZ")
    destination.mkdir(parents=True)
    summary = {"kind": "offline-harness-real-tools-scripted-model", "api_calls": 0,
               "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
               "python": platform.python_version(), "percentile_method": "p50 median; p99 nearest rank",
               "worker_utilization": None, "worker_utilization_reason": "Tool durations do not identify complete worker busy intervals.",
               "cases": {}}
    for case in ("simple", "code", "complex"):
        samples = [measure_request(case, i, destination) for i in range(1, args.repetitions + 1)]
        summary["cases"][case] = {"samples": samples, "metrics": metrics(samples, sum(s["seconds"] for s in samples))}
        print(case, json.dumps(summary["cases"][case]["metrics"]), flush=True)
    stress_dir = destination / "stress"
    stress_dir.mkdir()
    summary["stress"] = asyncio.run(stress(args.concurrency, stress_dir))
    print("stress", json.dumps(summary["stress"]["metrics"]), flush=True)
    profiler = cProfile.Profile()
    profiler.enable()
    profile_sample = measure_request("complex", "profile", destination)
    profiler.disable()
    buffer = io.StringIO()
    pstats.Stats(profiler, stream=buffer).sort_stats("cumulative").print_stats(20)
    (destination / "profile.txt").write_text(buffer.getvalue())
    profiler.dump_stats(str(destination / "profile.pstats"))
    summary["profile_sample"] = profile_sample
    (destination / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"Offline measurements saved: {destination}", flush=True)
    assert all(sample["success"] for case in summary["cases"].values() for sample in case["samples"])
    assert summary["stress"]["metrics"]["successes"] == args.concurrency and profile_sample["success"]


if __name__ == "__main__":
    main()
