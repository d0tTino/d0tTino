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
    assert cli_common._SESSION_TOKENS["process.exec"][0] == token


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


def test_session_log_records_grants_and_denials(monkeypatch, tmp_path):
    cli_common._SESSION_TOKENS.clear()
    monkeypatch.setattr(
        cli_common, "SESSION_LOG", tmp_path / "session.log"
    )
    inputs = iter(["y", "n", "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    def fake_run(cmd, *, shell, capture_output, text):
        class Result:
            def __init__(self):
                self.stdout = ""
                self.stderr = ""
                self.returncode = 0

        return Result()

    monkeypatch.setattr(cli_common.subprocess, "run", fake_run)

    steps = [
        PlanStep(1, "echo hi", capabilities={Capability.PROCESS_EXEC}),
        PlanStep(2, "curl example.com", capabilities={Capability.NETWORK_FETCH}),
        PlanStep(3, "cat file.txt", capabilities={Capability.FILESYSTEM_READ}),
    ]

    cli_common.execute_steps(steps, log_path=tmp_path / "log.txt", assume_yes=True)

    content = (tmp_path / "session.log").read_text()
    assert "[granted capability: process.exec" in content
    assert "[denied capability: network.fetch]" in content
    assert "[granted capability: filesystem.read" in content


def test_token_expiration(monkeypatch, tmp_path):
    cli_common._SESSION_TOKENS.clear()
    current = {"time": 1000.0}
    monkeypatch.setattr(cli_common.time, "time", lambda: current["time"])

    calls = {"count": 0}

    def fake_input(_: str) -> str:
        calls["count"] += 1
        return "y"

    monkeypatch.setattr("builtins.input", fake_input)

    def fake_run(cmd, *, shell, capture_output, text):
        class Result:
            def __init__(self):
                self.stdout = ""
                self.stderr = ""
                self.returncode = 0

        return Result()

    monkeypatch.setattr(cli_common.subprocess, "run", fake_run)

    step = PlanStep(1, "echo hi", capabilities={Capability.PROCESS_EXEC})
    log = tmp_path / "log.txt"
    cli_common.execute_steps([step], log_path=log, assume_yes=True)
    token1, expiry1 = cli_common._SESSION_TOKENS["process.exec"]

    current["time"] = expiry1 + 1
    cli_common.execute_steps([step], log_path=log, assume_yes=True)
    token2, expiry2 = cli_common._SESSION_TOKENS["process.exec"]

    assert calls["count"] == 2
    assert token1 != token2
    assert expiry2 > expiry1
