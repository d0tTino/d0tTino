import io
import contextlib

from scripts import ai_exec


def test_plans_and_runs_commands(monkeypatch):
    def fake_send(prompt, *, local=False, model=ai_exec.ai_router.DEFAULT_MODEL):
        assert "task" in prompt.lower()
        return "echo 1\necho 2"

    runs = []

    def fake_run(cmd, shell=True):
        runs.append(cmd)
        class R:
            returncode = 0
        return R()

    inputs = iter(["y", "n"])
    monkeypatch.setattr(ai_exec.ai_router, "send_prompt", fake_send)
    monkeypatch.setattr(ai_exec.subprocess, "run", fake_run)
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_exec.main(["do something", "--model", "m", "--local"])

    assert rc == 0
    assert runs == ["echo 1"]
    lines = out.getvalue().splitlines()
    assert "echo 1" in lines
    assert "echo 2" in lines


def test_stops_on_command_failure(monkeypatch):
    monkeypatch.setattr(
        ai_exec.ai_router,
        "send_prompt",
        lambda *_args, **_kwargs: "bad 1\necho 2",
    )

    runs = []
    def fake_run(cmd, shell=True):
        runs.append(cmd)
        class R:
            returncode = 1 if len(runs) == 1 else 0
        return R()

    monkeypatch.setattr(ai_exec.subprocess, "run", fake_run)
    monkeypatch.setattr("builtins.input", lambda _: "y")

    rc = ai_exec.main(["task"])
    assert rc == 1
    assert runs == ["bad 1"]
