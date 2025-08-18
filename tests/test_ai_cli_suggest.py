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
    monkeypatch.setattr(ai_suggest, "read_key", lambda: "1")

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
    assert captured["steps"][0].command == "echo hi [risk:info]"
    assert captured["kwargs"]["analytics"] is True
    payload = captured["kwargs"]["payload"]
    assert payload["goal"] == "goal"
    assert payload["context"] == "ctx"


def test_suggest_skips_on_keypress(monkeypatch):
    monkeypatch.setattr(ai_cli, "_session", {})
    monkeypatch.setattr(
        ai_suggest,
        "suggest",
        lambda goal, **kwargs: [{"command": "echo hi [risk:info]", "rationale": ""}],
    )
    monkeypatch.setattr(ai_suggest, "read_key", lambda: "q")

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
