"""Additional offline curator regression checks; all skills/results are temporary."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from langchain_core.messages import AIMessage

from lab.curator import curate_skills
from lab.testing import ScriptedChatModel


def run_checks():
    good = "---\nname: workflow-check\ndescription: Use when validating artifacts.\n---\nRun independent checks before completing."
    reply = f"=== SKILL: workflow-check ===\n{good}\n=== END ===\n"
    with TemporaryDirectory(prefix="curator-check-") as folder:
        root = Path(folder)
        source = root / "results/baseline"
        def save(name, record):
            path = source / name
            path.mkdir(parents=True)
            (path / "run.json").write_text(json.dumps(record))
            return path

        failed = {"role": "learn", "checks": [{"name": "verify_output", "passed": False, "detail": "RULE: synthetic feedback"}]}
        errored = save("errored", {**failed, "error": "Offline simulated provider quota error"})
        model = ScriptedChatModel(script=[AIMessage(content=reply)])
        assert curate_skills(root / "results", out_dir=root / "skills", model=model) == [] and model.calls == 0
        print("PASS curator: infrastructure failure does not trigger a model call")
        errored.joinpath("run.json").unlink()
        save("malformed", [])
        save("bad-checks", {"role": "learn", "checks": [None, "invalid", {}]})
        learn = save("usable", failed)
        learn.joinpath("trace.md").write_text("OLD-MARKER" + "x" * 6500 + "TAIL-MARKER")
        evaluation = save("eval", {"role": "eval", "checks": [{"name": "EVAL-MARKER", "passed": False}]})
        evaluation.joinpath("trace.md").mkdir()  # Reading this as a file would fail.
        model = ScriptedChatModel(script=[AIMessage(content=reply + reply)])
        paths = curate_skills(root / "results", out_dir=root / "skills", model=model)
        assert len(paths) == 1 and model.calls == 1
        assert "TAIL-MARKER" in model.prompts[0] and "OLD-MARKER" not in model.prompts[0]
        assert "EVAL-MARKER" not in model.prompts[0] and "synthetic feedback" in model.prompts[0]
        print("PASS curator: malformed input skipped, trace bounded, eval trace excluded, duplicates rejected")
        outside = root / "outside"
        outside.mkdir()
        linked = root / "linked-skills"
        linked.mkdir()
        linked.joinpath("workflow-check").symlink_to(outside, target_is_directory=True)
        model = ScriptedChatModel(script=[AIMessage(content=reply)])
        assert curate_skills(root / "results", out_dir=linked, model=model) == []
        assert not outside.joinpath("SKILL.md").exists()
        print("PASS curator: existing symlink cannot redirect a skill outside output")
        for cap in (0, -1):
            model = ScriptedChatModel(script=[AIMessage(content=reply)])
            try:
                result = curate_skills(root / "results", out_dir=root / "skills", model=model, max_skills=cap)
            except ValueError:
                assert cap == -1
            else:
                assert cap == 0 and result == []
            assert model.calls == 0
        print("PASS curator: zero and negative skill limits never consume model calls")


if __name__ == "__main__":
    run_checks()
