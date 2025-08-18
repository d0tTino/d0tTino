import re

from scripts import cli_common
from scripts.cli_common import PlanStep
from scripts.capabilities import Capability


def test_grant_capability_allows_execution(monkeypatch, tmp_path):
    cli_common._SESSION_TOKENS.clear()
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
    match = re.search(r"\[granted capability: process\.exec token=([0-9a-f]+)\]", content)
    assert match
    token = match.group(1)
    assert cli_common._SESSION_TOKENS["process.exec"] == token


def test_tokens_persist_for_session(monkeypatch, tmp_path):
    cli_common._SESSION_TOKENS.clear()
    calls = {"count": 0}

    def fake_input(_: str) -> str:
        calls["count"] += 1
        return "y"

    monkeypatch.setattr("builtins.input", fake_input)

    executed = []

    def fake_run(cmd, *, shell, capture_output, text):
        executed.append(cmd)

        class Result:
            def __init__(self):
                self.stdout = ""
                self.stderr = ""
                self.returncode = 0

        return Result()

    monkeypatch.setattr(cli_common.subprocess, "run", fake_run)

    step = PlanStep(1, "echo hi", capabilities={Capability.PROCESS_EXEC})
    log = tmp_path / "log.txt"
    rc1 = cli_common.execute_steps([step], log_path=log, assume_yes=True)
    rc2 = cli_common.execute_steps([step], log_path=log, assume_yes=True)

    assert rc1 == rc2 == 0
    assert calls["count"] == 1
    assert len(executed) == 2
    content = log.read_text()
    assert content.count("granted capability") == 1
    assert "using capability token: process.exec" in content
