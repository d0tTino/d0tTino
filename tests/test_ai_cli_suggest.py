import contextlib
import io

from scripts import ai_cli, ai_suggest, cli_actions


def test_suggest_executes_selected_command(monkeypatch):
    monkeypatch.setattr(ai_cli, "_session", {"context": "ctx"})
    monkeypatch.setattr(
        ai_suggest,
        "suggest",
        lambda goal, **kwargs: [{"command": "echo hi [risk:info]", "rationale": ""}],
    )
    inputs = iter([""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    captured = {}

    def fake_run_steps(event_name, steps, **kwargs):
        captured["event"] = event_name
        captured["steps"] = steps
        captured["kwargs"] = kwargs
        return 0

    monkeypatch.setattr(cli_actions, "run_steps", fake_run_steps)

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(["suggest", "goal", "--analytics"])
    assert rc == 0
    assert captured["event"] == "ai-cli-suggest-run"
    assert captured["steps"] == ["echo hi [risk:info]"]
    assert captured["kwargs"]["analytics"] is True
    payload = captured["kwargs"]["payload"]
    assert payload["goal"] == "goal"
    assert payload["context"] == "ctx"


def test_suggest_skips_on_input(monkeypatch):
    monkeypatch.setattr(ai_cli, "_session", {})
    monkeypatch.setattr(
        ai_suggest,
        "suggest",
        lambda goal, **kwargs: [{"command": "echo hi [risk:info]", "rationale": ""}],
    )
    inputs = iter(["n"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    calls = []

    def fake_run_steps(*args, **kwargs):
        calls.append((args, kwargs))
        return 0

    monkeypatch.setattr(cli_actions, "run_steps", fake_run_steps)

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(["suggest", "goal"])
    assert rc == 0
    assert calls == []
