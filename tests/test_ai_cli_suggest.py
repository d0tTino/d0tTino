import contextlib
import io
import pytest

pytest.importorskip("requests")

from scripts import ai_cli, ai_suggest


def test_suggest_subcommand(monkeypatch):
    suggestions = [
        "rm -rf / [risk:rm]",
        "sudo reboot now [risk:reboot]",
        "ls -la [risk:info]",
    ]

    def fake_suggest(goal, *, local=False, model=ai_cli.router.DEFAULT_MODEL, context=None):
        assert goal == "goal"
        assert local is True
        assert model == "m"
        return suggestions

    monkeypatch.setattr(ai_suggest, "suggest", fake_suggest)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(["suggest", "goal", "--local", "--model", "m"])
    assert rc == 0
    lines = out.getvalue().splitlines()
    assert lines == suggestions
    assert len(lines) == 3
    for line in lines:
        assert "[risk:" in line
