"""Summarize real learning run logs without exposing credentials or eval data.

Run: python report/debug_runs.py --results results --output report/performance/learning-debug.json
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path


def analyze(results_dir):
    runs = []
    for path in sorted(Path(results_dir).rglob("run.json")):
        if path.parent.name.endswith("-eval"):
            continue
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("role") != "learn":
            continue
        error = record.get("error") or ""
        if any(marker in error for marker in ("RateLimit", "429")):
            category = "provider-rate-limit"
        elif any(marker in error for marker in ("413", "BadRequest", "InvalidRequest", "ContextOverflow",
                                                "Authentication", "APIConnection", "APITimeout", "APIStatus")):
            category = "provider-request-or-transport"
        elif "GraphRecursionError" in error:
            category = "graph-iteration-limit"
        elif error:
            category = "other-execution-error"
        elif record.get("score") != 1:
            category = "task-check-failure"
        else:
            category = "success"
        trace_path = path.with_name("trace.md")
        trace = trace_path.read_text(encoding="utf-8") if trace_path.exists() else ""
        names = Counter(re.findall(r"^### Tool call: (\S+)", trace, re.M))
        tools = record.get("tool_executions", [])
        handoffs = record.get("communications", [])
        requests = Counter(event["id"] for event in handoffs if event["type"] == "task")
        replies = Counter(event["id"] for event in handoffs if event["type"] == "result")
        runs.append({"path": str(path), "task": record["task"], "condition": record["condition"],
                     "category": category, "error_type": error.split(":", 1)[0] if error else None,
                     "score": record["score"], "passed": record["passed"], "total": record["total"],
                     "seconds": record["seconds"], "tokens": record["tokens"],
                     "main_tool_calls": record["tool_calls"], "subagent_calls": record["subagent_calls"],
                     "trace_tool_counts": dict(names), "tool_event_counts": dict(Counter(e["name"] for e in tools)),
                     "pending_handoffs": sum((requests - replies).values()),
                     "errored_tools": sum(e["status"] == "error" for e in tools),
                     "unfinished_tools": sum(e["status"] == "running" for e in tools),
                     "worker_errors": len(record.get("worker_errors", []))})
    return {"kind": "real-learning-log-analysis", "runs": runs,
            "categories": dict(Counter(run["category"] for run in runs)),
            "record_count": len(runs), "tokens_total": sum(run["tokens"]["total"] for run in runs),
            "seconds_total": sum(run["seconds"] for run in runs),
            "successful_tasks": sum(run["category"] == "success" for run in runs),
            "note": "Errored runs retain raw checks but do not support task-quality conclusions. Nested tool durations overlap; do not add them as exclusive CPU time."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    parser.add_argument("--output", default="report/performance/learning-debug.json")
    args = parser.parse_args()
    result = analyze(args.results)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2))
    print(json.dumps({key: value for key, value in result.items() if key != "runs"}, indent=2))
