import pytest
from textual.widgets import Static, Input, Select

from ui.textual_app import TerminalUI


@pytest.mark.asyncio
async def test_prompt_routing(monkeypatch):
    calls = []

    def mock_send_prompt(prompt: str):
        calls.append(prompt)
        return f"resp:{prompt}"

    monkeypatch.setattr("ui.textual_app.send_prompt", mock_send_prompt)

    app = TerminalUI()
    async with app.run_test() as pilot:
        app.query_one("#prompt", Input).value = "hello"
        await pilot.click("#send")
        await pilot.pause()

        assert calls == ["hello"]
        assert str(app.query_one("#response", Static).renderable) == "resp:hello"


@pytest.mark.asyncio
async def test_palette_application(monkeypatch):
    calls = []

    def mock_apply_palette(name: str, repo_root):
        calls.append(name)

    monkeypatch.setattr("ui.textual_app.apply_palette", mock_apply_palette)

    app = TerminalUI()
    async with app.run_test() as pilot:
        app.query_one("#palette", Select).value = "dracula"
        await pilot.click("#apply")
        await pilot.pause()

        assert calls == ["dracula"]
        assert str(app.query_one("#status", Static).renderable) == "Applied dracula"

