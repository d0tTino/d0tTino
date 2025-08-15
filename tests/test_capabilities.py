from scripts import cli_common
from scripts.cli_common import PlanStep
from scripts.capabilities import Capability


def test_grant_capability_allows_execution(monkeypatch, tmp_path):
    inputs = iter(["y"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    executed = {}

    def fake_run(cmd, *, shell, capture_output, text):
        executed["called"] = True

        class Result:
            def __init__(self):
                self.stdout = ""
                self.stderr = ""
                self.returncode = 0

        return Result()

    monkeypatch.setattr(cli_common.subprocess, "run", fake_run)

    step = PlanStep(1, "echo hi", capabilities={Capability.PROCESS_EXEC})
    rc = cli_common.execute_steps(
        [step],
        log_path=tmp_path / "log.txt",
        assume_yes=True,
    )

    assert rc == 0
    assert executed["called"] is True
    content = (tmp_path / "log.txt").read_text()
    assert "[granted capability: process.exec]" in content
