"""Real provider benchmark on learning tasks only; preserves earlier results.

This sends learning instructions/files to the provider configured in .env.
Run: python report/benchmark_learn.py --repetitions 3
Stops the batch on an infrastructure/provider failure instead of retrying blindly.
"""
import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.rate_limiters import InMemoryRateLimiter

from lab.model import make_model
from lab.runner import run_task


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--recursion-limit", type=int, default=20)
    parser.add_argument("--request-interval", type=float, default=60)
    parser.add_argument("--max-runs", type=int, default=18)
    args = parser.parse_args()
    if min(args.repetitions, args.recursion_limit, args.max_runs) <= 0 or args.request_interval < 0:
        parser.error("repetitions, recursion limit and max runs must be positive; request interval cannot be negative")
    folder = Path("results/performance") / datetime.now(timezone.utc).strftime("groq-%Y%m%dT%H%M%S%fZ")
    folder.mkdir(parents=True)
    model = make_model()
    # Disable hidden SDK retries; failed attempts stay explicit in the records.
    model.client = model.root_client.with_options(max_retries=0).chat.completions
    model.async_client = model.root_async_client.with_options(max_retries=0).chat.completions
    model.max_retries = 0
    if args.request_interval:
        limiter = InMemoryRateLimiter(requests_per_second=1 / args.request_interval,
                                      check_every_n_seconds=.1, max_bucket_size=1)
        limiter.available_tokens = 1  # The first call can start immediately.
        model.rate_limiter = limiter
    configuration = {
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "model": os.getenv("LAB_MODEL"), "base_url": os.getenv("LAB_BASE_URL"),
        "temperature": os.getenv("LAB_TEMPERATURE", "0"),
        "max_input_tokens": os.getenv("LAB_MAX_INPUT_TOKENS"),
        "max_output_tokens": os.getenv("LAB_MAX_OUTPUT_TOKENS"),
        "recursion_limit": args.recursion_limit, "sdk_retries": 0,
        "output_limit": 10000, "repetitions": args.repetitions,
        "request_interval_seconds": args.request_interval, "max_runs": args.max_runs,
    }
    (folder / "configuration.json").write_text(json.dumps(configuration, indent=2))
    planned = [(iteration, condition, task) for iteration in range(1, args.repetitions + 1)
               for condition in ("baseline", "subagents")
               for task in ("code-learn", "data-learn", "logs-learn")]
    planned = planned[:args.max_runs]
    manifest = {"kind": "real-provider-learning", "planned_runs": len(planned), "runs": [], "stopped": None}
    print(f"Provider benchmark output: {folder}", flush=True)
    for iteration, condition, task in planned:
        record = run_task(task, condition, results_dir=folder / f"iteration-{iteration}",
                          model=model, recursion_limit=args.recursion_limit)
        manifest["runs"].append({"iteration": iteration, "condition": condition, "task": task,
                                 "seconds": record["seconds"], "score": record["score"],
                                 "tokens": record["tokens"], "error": record["error"]})
        print(f"{iteration} {condition} {task}: {record['passed']}/{record['total']}, "
              f"tokens={record['tokens']['total']}, seconds={record['seconds']}, "
              f"error_type={(record['error'] or '').split(':', 1)[0] or None}", flush=True)
        error = record.get("error") or ""
        if any(marker in error for marker in ("RateLimit", "BadRequest", "InvalidRequest", "ContextOverflow", "NotFound", "Authentication", "PermissionDenied",
                                              "APIConnection", "APITimeout", "APIStatus", "413", "429")):
            manifest["stopped"] = "Provider/infrastructure failure; inspect the saved run.json before resuming."
        manifest["pending_runs"] = len(planned) - len(manifest["runs"])
        (folder / "manifest.json").write_text(json.dumps(manifest, indent=2))
        if manifest["stopped"]:
            print(manifest["stopped"], flush=True)
            break
    return 1 if manifest["stopped"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
