import contextlib
import io

import pytest

pytest.importorskip("requests")

from scripts import ai_suggest


def test_ai_suggest_risk_tagging(monkeypatch):
    lines = [
        "rm -rf /",
        "sudo reboot now",
        "ls -la",
        "echo hi",
    ]

    def fake(goal, *, local=False, model=ai_suggest.router.DEFAULT_MODEL, context=None):
        assert goal == "goal"
        return lines

    monkeypatch.setattr(ai_suggest.router, "shell_suggest", fake)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_suggest.main(["goal", "--local", "--model", "m"])
    assert rc == 0
    suggestions = out.getvalue().splitlines()
    assert len(suggestions) == 3
    assert suggestions[0].endswith("[risk:rm]")
    assert suggestions[1].endswith("[risk:reboot]")
    assert suggestions[2].endswith("[risk:info]")
    for line in suggestions:
        assert "[risk:" in line
