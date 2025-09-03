import pytest
import uuid

pytest.importorskip("requests")
from scripts import cli_common
from scripts.cli_common import PlanStep
from scripts.capabilities import Capability


def test_record_event_skips_when_disabled(monkeypatch):
    monkeypatch.setenv("EVENTS_URL", "https://example.com")
    called = []

    def fake_post(url, headers=None, json=None, timeout=None):
        called.append(True)

    monkeypatch.setattr(cli_common.requests, "post", fake_post)
    cli_common.record_event("name", {"a": 1}, enabled=False)
    assert not called


def test_record_event_posts(monkeypatch):
    monkeypatch.setenv("EVENTS_URL", "https://example.com")
    monkeypatch.setenv("EVENTS_TOKEN", "tok")
    monkeypatch.setenv("USER", "alice")
    sent = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        sent["url"] = url
        sent["headers"] = headers
        sent["data"] = json

        class Resp:
            status_code = 200

        return Resp()

    monkeypatch.setattr(cli_common.requests, "post", fake_post)
    cli_common.record_event("name", {"a": 1}, enabled=True)

    assert sent["url"] == "https://example.com"
    expected_dev = uuid.uuid5(uuid.NAMESPACE_DNS, "alice").hex
    assert sent["data"] == {
        "payload": {"name": "name", "a": 1, "developer": expected_dev}
    }
    assert sent["headers"]["Authorization"] == "Bearer tok"


def test_record_event_requires_url(monkeypatch):
    called = []

    def fake_post(url, headers=None, json=None, timeout=None):
        called.append(True)

    monkeypatch.setattr(cli_common.requests, "post", fake_post)
    monkeypatch.delenv("EVENTS_URL", raising=False)
    cli_common.record_event("name", {"a": 1}, enabled=True)

    assert not called


def test_record_event_empty_url(monkeypatch):
    monkeypatch.setenv("EVENTS_URL", "")
    called = []

    def fake_post(url, headers=None, json=None, timeout=None):
        called.append(True)

    monkeypatch.setattr(cli_common.requests, "post", fake_post)
    cli_common.record_event("name", {"a": 1}, enabled=True)

    assert not called


def test_record_event_accepts_invalid_timestamps(monkeypatch):
    monkeypatch.setenv("EVENTS_URL", "https://example.com")
    sent = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        sent.update({"url": url, "data": json})

        class Resp:
            status_code = 200

        return Resp()

    monkeypatch.setattr(cli_common.requests, "post", fake_post)
    cli_common.record_event(
        "ai-do",
        {"end_ts": "not-a-number", "exit_code": 0},
        enabled=True,
    )

    assert sent["data"]["payload"]["end_ts"] == "not-a-number"



def test_analytics_default(monkeypatch):
    monkeypatch.setenv("EVENTS_ENABLED", "yes")
    assert cli_common.analytics_default() is True
    monkeypatch.setenv("EVENTS_ENABLED", "0")
    assert cli_common.analytics_default() is False


def test_execute_steps_parses_quoted_args(monkeypatch, tmp_path):
    inputs = iter(["y", "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    captured = {}

    def fake_run(cmd, *, shell, capture_output, text):
        captured["cmd"] = cmd
        captured["shell"] = shell

        class Result:
            def __init__(self):
                self.stdout = ""
                self.stderr = ""
                self.returncode = 0

        return Result()

    monkeypatch.setattr(cli_common.subprocess, "run", fake_run)

    cli_common.execute_steps(
        [PlanStep(1, "echo 'foo bar'")],
        log_path=tmp_path / "log.txt",
        dry_run_log=["1. echo 'foo bar'"]
    )

    assert captured["cmd"] == ["echo", "foo bar"]
    assert captured["shell"] is False


def test_execute_steps_fallbacks_to_shell(monkeypatch, tmp_path):
    inputs = iter(["y", "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    captured = {}

    def fake_run(cmd, *, shell, capture_output, text):
        captured["cmd"] = cmd
        captured["shell"] = shell

        class Result:
            def __init__(self):
                self.stdout = ""
                self.stderr = ""
                self.returncode = 0

        return Result()

    monkeypatch.setattr(cli_common.subprocess, "run", fake_run)

    cli_common.execute_steps(
        [PlanStep(1, "python -c \"print('hi')\"")],
        log_path=tmp_path / "log.txt",
        dry_run_log=["1. python -c \"print('hi')\""]
    )

    assert captured["cmd"] == "python -c \"print('hi')\""
    assert captured["shell"] is True


def test_execute_steps_windows_path(monkeypatch, tmp_path):
    inputs = iter(["y", "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    captured = {}

    def fake_run(cmd, *, shell, capture_output, text):
        captured["cmd"] = cmd
        captured["shell"] = shell

        class Result:
            def __init__(self):
                self.stdout = ""
                self.stderr = ""
                self.returncode = 0

        return Result()

    monkeypatch.setattr(cli_common.subprocess, "run", fake_run)
    monkeypatch.setattr(cli_common.os, "name", "nt")

    cli_common.execute_steps(
        [PlanStep(1, '"C:\\Program Files\\Foo Bar\\tool.exe" arg')],
        log_path=tmp_path / "log.txt",
        dry_run_log=["1. \"C:/Program Files/Foo Bar/tool.exe\" arg"],
    )

    assert captured["cmd"] == ["C:\\Program Files\\Foo Bar\\tool.exe", "arg"]
    assert captured["shell"] is False


def test_execute_steps_enforces_capabilities(monkeypatch, tmp_path):
    cli_common._SESSION_TOKENS.clear()
    inputs = iter(["n"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    captured = {}

    def fake_run(cmd, *, shell, capture_output, text):
        captured["called"] = True

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
        allowed_capabilities={Capability.FILESYSTEM_READ},
        assume_yes=True,
        dry_run_log=["1. echo hi"],
    )

    assert rc == 1
    assert "called" not in captured
    content = (tmp_path / "log.txt").read_text()
    assert "missing capabilities: process.exec" in content


def test_execute_steps_logs_capabilities(monkeypatch, tmp_path):
    inputs = iter(["y", "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    def fake_run(cmd, *, shell, capture_output, text):
        class Result:
            def __init__(self):
                self.stdout = ""
                self.stderr = ""
                self.returncode = 0

        return Result()

    monkeypatch.setattr(cli_common.subprocess, "run", fake_run)

    step = PlanStep(1, "echo hi", capabilities={Capability.PROCESS_EXEC})
    cli_common.execute_steps(
        [step],
        log_path=tmp_path / "log.txt",
        allowed_capabilities={Capability.PROCESS_EXEC},
        dry_run_log=["1. echo hi"],
    )

    content = (tmp_path / "log.txt").read_text()
    assert "[capabilities: process.exec]" in content


def test_execute_steps_reuses_dry_run_log(monkeypatch, tmp_path, capsys):
    step = PlanStep(1, "echo hi")
    log = tmp_path / "log.txt"
    dry_log: list[str] = []
    cli_common.execute_steps([step], log_path=log, dry_run=True, dry_run_log=dry_log)
    assert dry_log
    capsys.readouterr()

    def fake_run(cmd, *, shell, capture_output, text):
        class Result:
            def __init__(self):
                self.stdout = "done"
                self.stderr = ""
                self.returncode = 0

        return Result()

    monkeypatch.setattr(cli_common.subprocess, "run", fake_run)
    cli_common.execute_steps([step], log_path=log, dry_run_log=dry_log, assume_yes=True)
    out = capsys.readouterr().out.splitlines()
    assert out.count("1. echo hi") == 1
    assert "$ echo hi" in out


def test_execute_steps_requires_confirmation_after_dry_run(monkeypatch, tmp_path, capsys):
    step = PlanStep(1, "echo hi")
    log = tmp_path / "log.txt"
    dry_log: list[str] = []
    cli_common.execute_steps([step], log_path=log, dry_run=True, dry_run_log=dry_log)
    assert dry_log
    capsys.readouterr()

    called = False

    def fake_run(cmd, *, shell, capture_output, text):
        nonlocal called
        called = True

        class Result:
            def __init__(self):
                self.stdout = ""
                self.stderr = ""
                self.returncode = 0

        return Result()

    monkeypatch.setattr(cli_common.subprocess, "run", fake_run)
    monkeypatch.setattr("builtins.input", lambda _: "n")
    rc = cli_common.execute_steps([step], log_path=log, dry_run_log=dry_log)
    assert rc == 1
    assert not called
