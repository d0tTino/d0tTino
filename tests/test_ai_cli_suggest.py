import contextlib
import io

import contextlib
import io

from scripts import ai_cli, ai_suggest, cli_actions


def test_suggest_executes_selected_command(monkeypatch):
    monkeypatch.setattr(ai_cli, "_session", {"context": "ctx"})
    monkeypatch.setattr(
        ai_suggest,
        "suggest",
        lambda goal, **kwargs: [
            {"command": "echo hi", "rationale": "", "risk": {"tags": ["info"], "score": 0}}
        ],
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
        lambda goal, **kwargs: [
            {"command": "echo hi", "rationale": "", "risk": {"tags": ["info"], "score": 0}}
        ],
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


def test_suggest_forwards_to_plan(monkeypatch):
    monkeypatch.setattr(ai_cli, "_session", {})
    monkeypatch.setattr(
        ai_suggest,
        "suggest",
        lambda goal, **kwargs: [
            {"command": "echo hi", "rationale": "", "risk": {"tags": ["info"], "score": 0}}
        ],
    )
    monkeypatch.setattr(ai_suggest, "read_key", lambda: "1")

    captured = {}

    def fake_plan(args):
        captured["goal"] = args.goal
        captured["analytics"] = args.analytics
        return 0

    def forbid_run_steps(*args, **kwargs):  # pragma: no cover - ensure not called
        raise AssertionError("run_steps should not be called")

    monkeypatch.setattr(ai_cli, "_cmd_plan", fake_plan)
    monkeypatch.setattr(cli_actions, "run_steps", forbid_run_steps)

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(["suggest", "goal", "--to-plan", "--analytics"])
    assert rc == 0
    assert captured["goal"] == "echo hi"
    assert captured["analytics"] is True
