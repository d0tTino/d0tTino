import io
import contextlib
import subprocess
from pathlib import Path
import pytest

pytest.importorskip("requests")

from scripts import ai_do, ai_exec, cli_actions
from scripts.cli_common import PlanStep


def test_main_runs_and_logs(monkeypatch, tmp_path):
    def fake_plan(goal: str, *, config_path=None, analytics=False):
        assert goal == "goal"
        assert config_path is None
        return [PlanStep(1, "cmd1"), PlanStep(2, "cmd2")]

    monkeypatch.setattr(ai_exec, "plan", fake_plan)

    calls = []

    def fake_run(cmd, *, shell, capture_output, text):
        assert not shell and capture_output and text
        calls.append(cmd)

        class Result:
            def __init__(self):
                self.stdout = f"out:{cmd}\n"
                self.stderr = ""
                self.returncode = 0

        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)

    inputs = iter(["y", "n"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    log = tmp_path / "log.txt"
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_do.main(["goal", "--log", str(log)])

    assert rc == 0
    assert calls == [["cmd1"]]
    assert "$ cmd1" in log.read_text()


def test_main_skips_when_declined(monkeypatch, tmp_path):
    monkeypatch.setattr(ai_exec, "plan", lambda *a, **k: [PlanStep(1, "cmd")])
    monkeypatch.setattr("builtins.input", lambda _: "n")
    run_called = False

    def fail_run(*args, **kwargs):
        nonlocal run_called
        run_called = True

    monkeypatch.setattr(subprocess, "run", fail_run)

    log = tmp_path / "log.txt"
    rc = ai_do.main(["goal", "--log", str(log)])

    assert rc == 0
    assert not run_called
    assert not log.exists()


def test_main_dry_run(monkeypatch, tmp_path):
    monkeypatch.setattr(
        ai_exec,
        "plan",
        lambda *a, **k: [PlanStep(1, "echo hi", diff="--- a\n+++ b\n+hi")],
    )
    def fail_run(*a, **k):
        raise AssertionError("run called")

    monkeypatch.setattr(subprocess, "run", fail_run)
    log = tmp_path / "log.txt"
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_do.main(["goal", "--log", str(log), "--dry-run"])
    assert rc == 0
    assert "1. echo hi" in out.getvalue()
    assert "--- a" in out.getvalue()
    assert "dry-run" in log.read_text()


def test_diff_preview_shown(monkeypatch, tmp_path):
    monkeypatch.setattr(
        ai_exec,
        "plan",
        lambda *a, **k: [PlanStep(1, "echo hi", diff="--- a\n+++ b\n+hi")],
    )

    run_called = False

    def fail_run(*a, **k):
        nonlocal run_called
        run_called = True

    monkeypatch.setattr(subprocess, "run", fail_run)

    prompts = []

    def fake_input(prompt):
        prompts.append(prompt)
        return "n"

    monkeypatch.setattr("builtins.input", fake_input)

    log = tmp_path / "log.txt"
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_do.main(["goal", "--log", str(log)])

    assert rc == 0
    output = out.getvalue()
    assert "--- a" in output
    assert not run_called
    assert prompts and prompts[0].startswith("Run command")


def test_main_yes_runs_without_prompts(monkeypatch, tmp_path):
    monkeypatch.setattr(ai_exec, "plan", lambda *a, **k: [PlanStep(1, "echo hi")])

    called = []

    def fake_run(cmd, *, shell, capture_output, text):
        called.append(cmd)

        class Result:
            def __init__(self):
                self.stdout = ""
                self.stderr = ""
                self.returncode = 0

        return Result()

    def fail_input(_):  # pragma: no cover - should not be called
        raise AssertionError("input called")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("builtins.input", fail_input)
    log = tmp_path / "log.txt"
    rc = ai_do.main(["goal", "--log", str(log), "--yes"])
    assert rc == 0
    assert called == [["echo", "hi"]]


def test_risky_requires_confirm(monkeypatch, tmp_path):
    monkeypatch.setattr(
        ai_exec, "plan", lambda *a, **k: [PlanStep(1, "rm -rf / [risk:rm]")]
    )
    prompts = []

    def fake_input(prompt):
        prompts.append(prompt)
        return "n"

    def fail_run(*a, **k):
        raise AssertionError("should not run")

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr(subprocess, "run", fail_run)
    log = tmp_path / "log.txt"
    rc = ai_do.main(["goal", "--log", str(log), "--yes"])
    assert rc == 1
    assert not prompts


def test_confirm_allows_risky(monkeypatch, tmp_path):
    monkeypatch.setattr(
        ai_exec, "plan", lambda *a, **k: [PlanStep(1, "echo hi [risk:rm]")]
    )
    called = []

    def fake_run(cmd, *, shell, capture_output, text):
        called.append(cmd)

        class Result:
            def __init__(self):
                self.stdout = ""
                self.stderr = ""
                self.returncode = 0

        return Result()

    def fail_input(_):  # pragma: no cover - should not be called
        raise AssertionError("input called")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("builtins.input", fail_input)
    log = tmp_path / "log.txt"
    rc = ai_do.main(["goal", "--log", str(log), "--yes", "--confirm"])
    assert rc == 0
    assert called == [["echo", "hi"]]


def test_main_returns_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(ai_exec, "plan", lambda *a, **k: [PlanStep(1, "fail")])

    class Result:
        def __init__(self):
            self.stdout = ""
            self.stderr = "err"
            self.returncode = 1

    def fake_run(cmd, *, shell, capture_output, text):
        assert not shell and capture_output and text
        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)
    inputs = iter(["y"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    log = tmp_path / "log.txt"
    rc = ai_do.main(["goal", "--log", str(log)])

    assert rc == 1
    assert "(exit 1)" in log.read_text()


def test_main_confirms_and_sanitizes(monkeypatch, tmp_path):
    monkeypatch.setattr(ai_exec, "plan", lambda *a, **k: [PlanStep(1, "echo hi")])

    prompts = []
    inputs = iter(["y"])

    def fake_input(prompt):
        prompts.append(prompt)
        return next(inputs)

    def fake_run(cmd, *, shell, capture_output, text):
        assert cmd == ["echo", "hi"]
        assert not shell and capture_output and text

        class Result:
            def __init__(self):
                self.stdout = ""
                self.stderr = ""
                self.returncode = 0

        return Result()

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr(subprocess, "run", fake_run)

    log = tmp_path / "log.txt"
    rc = ai_do.main(["goal", "--log", str(log)])

    assert rc == 0
    assert any(prompt.startswith("Run command: echo hi") for prompt in prompts)


def test_main_notifies(monkeypatch, tmp_path):
    monkeypatch.setattr(ai_exec, "plan", lambda *a, **k: [])
    monkeypatch.setattr("builtins.input", lambda _: "n")
    called = []

    def fake_notify(msg):
        called.append(msg)

    monkeypatch.setattr(ai_do, "send_notification", fake_notify)
    log = tmp_path / "log.txt"
    rc = ai_do.main(["goal", "--log", str(log), "--notify"])

    assert rc == 0
    assert called == ["ai-do completed with exit code 0"]


def test_main_records_event(monkeypatch, tmp_path):
    monkeypatch.setattr(ai_exec, "plan", lambda *a, **k: [])
    monkeypatch.setattr("builtins.input", lambda _: "n")
    recorded = []

    def fake_record(name, payload, *, enabled=False):
        recorded.append((name, payload, enabled))
        return True

    monkeypatch.setattr(cli_actions, "record_event_logged", fake_record)
    log = tmp_path / "log.txt"
    rc = ai_do.main(["goal", "--log", str(log), "--analytics"])

    assert rc == 0
    name, payload, enabled = recorded[0]
    assert name == "ai-do"
    assert enabled is True
    assert payload["goal"] == "goal"
    assert payload["exit_code"] == 0
    assert "duration_ms" in payload and payload["duration_ms"] >= 0
    assert payload["model_source"] == "remote"


def test_main_records_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(ai_exec, "plan", lambda *a, **k: [PlanStep(1, "bad")])
    inputs = iter(["y"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    class Result:
        def __init__(self):
            self.stdout = ""
            self.stderr = ""
            self.returncode = 1

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: Result())

    recorded = []

    def fake_record(name, payload, *, enabled=False):
        recorded.append((name, payload, enabled))
        return True

    monkeypatch.setattr(cli_actions, "record_event_logged", fake_record)
    log = tmp_path / "log.txt"
    rc = ai_do.main(["goal", "--log", str(log), "--analytics"])

    assert rc == 1
    name, payload, enabled = recorded[0]
    assert name == "ai-do"
    assert enabled is True
    assert payload["goal"] == "goal"
    assert payload["exit_code"] == 1
    assert "duration_ms" in payload and payload["duration_ms"] >= 0
    assert payload["model_source"] == "remote"


def test_main_accepts_config_path(monkeypatch):
    def fake_plan(goal: str, *, config_path=None, analytics=False):
        assert goal == "goal"
        assert config_path == Path("file.json")
        return []

    monkeypatch.setattr(ai_exec, "plan", fake_plan)
    monkeypatch.setattr("builtins.input", lambda _: "n")

    rc = ai_do.main(["goal", "--config", "file.json"])

    assert rc == 0


def test_main_accepts_sample_config(monkeypatch):
    def fake_plan(goal: str, *, config_path=None, analytics=False):
        assert goal == "goal"
        assert isinstance(config_path, Path)
        assert config_path == Path("sample.json")
        return []

    monkeypatch.setattr(ai_exec, "plan", fake_plan)
    monkeypatch.setattr("builtins.input", lambda _: "n")

    rc = ai_do.main(["goal", "--config", "sample.json"])

    assert rc == 0
