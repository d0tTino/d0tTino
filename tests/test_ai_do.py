import io
import contextlib
import subprocess

from scripts import ai_do, ai_exec


def test_main_runs_and_logs(monkeypatch, tmp_path):
    def fake_plan(goal: str, *, config_path=None):
        assert goal == "goal"
        assert config_path is None
        return ["cmd1", "cmd2"]

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

    inputs = iter(["y", "y", "n"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    log = tmp_path / "log.txt"
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_do.main(["goal", "--log", str(log)])

    assert rc == 0
    assert calls == [["cmd1"]]
    assert "$ cmd1" in log.read_text()


def test_main_skips_when_declined(monkeypatch, tmp_path):
    monkeypatch.setattr(ai_exec, "plan", lambda *a, **k: ["cmd"])
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


def test_main_returns_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(ai_exec, "plan", lambda *a, **k: ["fail"])

    class Result:
        def __init__(self):
            self.stdout = ""
            self.stderr = "err"
            self.returncode = 1

    def fake_run(cmd, *, shell, capture_output, text):
        assert not shell and capture_output and text
        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)
    inputs = iter(["y", "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    log = tmp_path / "log.txt"
    rc = ai_do.main(["goal", "--log", str(log)])

    assert rc == 1
    assert "(exit 1)" in log.read_text()


def test_main_confirms_and_sanitizes(monkeypatch, tmp_path):
    monkeypatch.setattr(ai_exec, "plan", lambda *a, **k: ["echo hi"])

    prompts = []
    inputs = iter(["y", "y"])

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
