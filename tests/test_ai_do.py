import io
import contextlib
import subprocess

from scripts import ai_do


def test_run_commands_respects_user_input(monkeypatch):
    runs = []

    def fake_run(cmd, shell=True):
        runs.append(cmd)
        class R:
            returncode = 0
        return R()

    inputs = iter(["y", "n"])
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_do.run_commands(["echo 1", "echo 2"])

    assert rc == 0
    assert runs == ["echo 1"]
    lines = out.getvalue().splitlines()
    assert "echo 1" in lines
    assert "echo 2" in lines


def test_run_commands_stops_on_failure(monkeypatch):
    runs = []
    def fake_run(cmd, shell=True):
        runs.append(cmd)
        class R:
            returncode = 1 if len(runs) == 1 else 0
        return R()

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("builtins.input", lambda _: "y")

    rc = ai_do.run_commands(["bad", "ok"])
    assert rc == 1
    assert runs == ["bad"]
