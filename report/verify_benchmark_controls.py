"""Offline orchestration checks; simulated manifests exist only in a temporary cwd."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

import benchmark_learn


def verify_controls(error, cap, interval):
    client = SimpleNamespace()
    client.with_options = lambda **kwargs: SimpleNamespace(chat=SimpleNamespace(completions=None))
    model = SimpleNamespace(root_client=client, root_async_client=client)
    simulated = {"passed": 0, "total": 1, "score": 0, "seconds": 0,
                 "tokens": {"input": 0, "output": 0, "total": 0}, "error": error}
    previous = Path.cwd()
    with TemporaryDirectory(prefix="benchmark-control-") as folder:
        try:
            os.chdir(folder)
            with patch("sys.argv", ["benchmark_learn.py", "--repetitions", "3", "--max-runs", str(cap), "--request-interval", str(interval)]), \
                 patch("benchmark_learn.make_model", return_value=model), \
                 patch("benchmark_learn.run_task", return_value=simulated) as invoke, \
                 patch("benchmark_learn.subprocess.check_output", return_value="offline-test-revision"):
                status = benchmark_learn.main()
            if error:
                assert status == 1 and invoke.call_count == 1, "Provider failure must stop before the next task"
            else:
                assert status == 0 and invoke.call_count == cap
            assert all(call.args[0].endswith("-learn") for call in invoke.call_args_list)
            assert hasattr(model, "rate_limiter") == bool(interval)
        finally:
            os.chdir(previous)
    print(f"PASS benchmark control: {error or 'cap'}, {cap=}, {interval=}; no API or persistent simulated results")


if __name__ == "__main__":
    verify_controls("OpenAIInvalidRequestError: offline simulated HTTP 400", 17, 60)
    verify_controls("OpenAIRateLimitError: offline simulated HTTP 429", 17, 60)
    verify_controls(None, 2, 0)
