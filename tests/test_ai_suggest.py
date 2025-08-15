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
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_suggest.main(["goal", "--local", "--model", "m"])
    assert rc == 0
    lines = out.getvalue().splitlines()
    assert len(lines) == 9  # 3 suggestions * 3 lines each
    assert lines[0].endswith("[risk:rm]")
    assert lines[1] == "wipe everything"
    assert lines[2] == "Press Enter to run"
    assert lines[3].endswith("[risk:reboot]")
    assert lines[4] == "restart"
    assert lines[5] == "Press Enter to run"
    assert lines[6].endswith("[risk:info]")
    assert lines[7] == "list"
    assert lines[8] == "Press Enter to run"


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
