import contextlib
import io
import subprocess

from scripts import ai_cli


def test_send_subcommand(monkeypatch):
    def mock_send(prompt, *, local=False, model=ai_cli.router.DEFAULT_MODEL):
        assert prompt == "msg"
        assert local is True
        assert model == "m"
        return "ok"

    monkeypatch.setattr(ai_cli.router, "send_prompt", mock_send)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(["send", "--local", "--model", "m", "msg"])
    assert rc == 0
    assert out.getvalue().strip() == "ok"


def test_plan_subcommand(monkeypatch):
    def fake_plan(goal: str, *, config_path=None):
        assert goal == "goal"
        assert config_path == "cfg.json"
        return ["one", "two"]

    monkeypatch.setattr(ai_cli.ai_exec, "plan", fake_plan)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(["plan", "goal", "--config", "cfg.json"])
    assert rc == 0
    assert out.getvalue().splitlines() == ["one", "two"]


def test_do_subcommand(monkeypatch, tmp_path):
    monkeypatch.setattr(ai_cli.ai_exec, "plan", lambda *a, **k: ["echo hi"])

    inputs = iter(["y", "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    def fake_run(cmd, *, shell, capture_output, text):
        assert cmd == ["echo", "hi"]
        class Result:
            def __init__(self):
                self.stdout = ""
                self.stderr = ""
                self.returncode = 0
        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)

    log = tmp_path / "log.txt"
    rc = ai_cli.main(["do", "goal", "--log", str(log)])
    assert rc == 0
    assert log.exists()
