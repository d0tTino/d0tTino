import contextlib
import io
import json

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


def test_ai_suggest_risk_tagging_and_rationale(monkeypatch):
    monkeypatch.setattr(ai_suggest.router, "shell_suggest", _fake_suggestions)
    def _fake_input(prompt: str = "") -> str:
        print(prompt)
        return ""

    monkeypatch.setattr("builtins.input", _fake_input)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_suggest.main(["goal", "--local", "--model", "m"])
    assert rc == 0
    lines = out.getvalue().splitlines()
    assert len(lines) == 7  # 3 suggestions * 2 lines + 1 prompt
    assert lines[0].startswith("1. ") and lines[0].endswith("[risk:rm]")
    assert lines[1] == "wipe everything"
    assert lines[2].startswith("2. ") and lines[2].endswith("[risk:reboot]")
    assert lines[3] == "restart"
    assert lines[4].startswith("3. ") and lines[4].endswith("[risk:info]")
    assert lines[5] == "list"
    assert lines[6].startswith("Select command to run")


def test_ai_suggest_json_output(monkeypatch):
    monkeypatch.setattr(ai_suggest.router, "shell_suggest", _fake_suggestions)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_suggest.main(["goal", "--json"])
    assert rc == 0
    data = json.loads(out.getvalue())
    assert len(data) == 3
    assert data[0]["command"].endswith("[risk:rm]")
    assert data[0]["rationale"] == "wipe everything"
