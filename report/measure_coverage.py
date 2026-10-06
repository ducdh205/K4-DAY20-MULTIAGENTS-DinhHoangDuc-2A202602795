"""Measure src/lab coverage using original pytest plus offline regressions.

Requires coverage in the virtualenv. No provider requests or persistent skills.
"""
import json
import runpy
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import coverage
import pytest


if __name__ == "__main__":
    destination = Path("report/performance")
    destination.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="coverage-check-") as folder:
        collector = coverage.Coverage(source=[str(Path("src/lab").resolve())],
                                      data_file=str(Path(folder) / ".coverage"), concurrency=["thread"])
        collector.start()
        # Save actual pytest/helper output for debugging and reproduction.
        import contextlib
        with (destination / "verification.log").open("w", encoding="utf-8") as output:
            with contextlib.redirect_stdout(output):
                exit_code = pytest.main(["tests", "-v", "--durations=10"])
                for script in ("verify_curator.py", "verify_worker_communication.py", "verify_tool_integration.py"):
                    runpy.run_path(str(Path("report") / script), run_name="__main__")
        collector.stop()
        collector.save()
        percent = collector.json_report(outfile=str(destination / "coverage.json"))
        result = {"coverage_version": coverage.__version__, "coverage_percent": percent,
                  "source": "all src/lab modules", "pytest_exit_code": int(exit_code),
                  "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()}
        (destination / "coverage-summary.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        assert exit_code == 0
