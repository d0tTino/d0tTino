import contextlib
import io
import contextlib
import io
import json
import shlex

import pytest

pytest.importorskip("requests")

from scripts import ai_suggest


def _fake_suggestions(goal, *, local=False, model=ai_suggest.router.DEFAULT_MODEL, context=None):
    assert goal.startswith("goal")
    return [
        "rm -rf / # wipe everything",
        "sudo reboot now # restart",
        "ls -la # list",
        "echo hi # greet",
    ]


def _fake_help(cmd: str) -> str:
    tokens = shlex.split(cmd)
    prog = tokens[1] if tokens and tokens[0] == "sudo" else tokens[0]
    return f"{prog} help"


def test_ai_suggest_risk_tagging_and_rationale(monkeypatch):
    monkeypatch.setattr(ai_suggest.router, "shell_suggest", _fake_suggestions)
    monkeypatch.setattr(ai_suggest, "_short_help", _fake_help)
    monkeypatch.setattr(ai_suggest, "read_key", lambda: "")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_suggest.main(["goal", "--local", "--model", "m"])
    assert rc == 0
    lines = out.getvalue().splitlines()
    assert len(lines) == 7  # 3 suggestions * 2 lines + 1 prompt
    assert lines[0].startswith("1. rm -rf /") and "[risk:write] (score:3)" in lines[0]
    assert lines[1] == "wipe everything (rm help)"
    assert lines[2].startswith("2. sudo reboot now") and "[risk:elevated] (score:4)" in lines[2]
    assert lines[3] == "restart (reboot help)"
    assert lines[4].startswith("3. ls -la") and "[risk:read] (score:1)" in lines[4]
    assert lines[5] == "list (ls help)"
    assert lines[6].startswith("Press [1-3] to run")


def test_ai_suggest_json_output(monkeypatch):
    monkeypatch.setattr(ai_suggest.router, "shell_suggest", _fake_suggestions)
    monkeypatch.setattr(ai_suggest, "_short_help", _fake_help)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_suggest.main(["goal", "--json"])
    assert rc == 0
    data = json.loads(out.getvalue())
    assert len(data) == 3
    assert data[0]["command"] == "rm -rf /"
    assert data[0]["risk"]["tags"] == ["write"]
    assert data[0]["risk"]["score"] == 3
    assert data[0]["rationale"] == "wipe everything (rm help)"


def _fake_suggestions_no_rationale(goal, *, local=False, model=ai_suggest.router.DEFAULT_MODEL, context=None):
    return ["ls"]


def test_ai_suggest_help_when_no_rationale(monkeypatch):
    monkeypatch.setattr(ai_suggest.router, "shell_suggest", _fake_suggestions_no_rationale)
    monkeypatch.setattr(ai_suggest, "_short_help", lambda cmd: "ls help")
    suggestions = ai_suggest.suggest("goal")
    assert suggestions[0]["rationale"] == "ls help"
