"""Offline tools checks with real local execution and synthetic temporary fixtures.

No API calls, provided task/test changes, or benchmark results.
Run in WSL: .venv/bin/python report/verify_tool_integration.py
"""
import os
import shlex
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from lab.agent import make_backend


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


if __name__ == "__main__":
    verify_backend()
