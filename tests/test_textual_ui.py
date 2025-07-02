import pytest
pytest.importorskip("textual")
from textual.widgets import Static, Input, Select  # noqa: E402 - imported after importorskip
from textual.command import CommandPalette
from ui.textual_app import PlanOverlay

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


@pytest.mark.asyncio
async def test_command_palette_hotkey():
    app = TerminalUI()
    async with app.run_test() as pilot:
        await pilot.press("ctrl+p")
        await pilot.pause(0.05)
        assert any(isinstance(s, CommandPalette) for s in app.screen_stack)


@pytest.mark.asyncio
async def test_plan_overlay_timeout():
    app = TerminalUI()
    async with app.run_test() as pilot:
        overlay = PlanOverlay(["step"], timeout=0.1)
        app.push_screen(overlay)
        assert overlay in app.screen_stack
        await pilot.pause(0.2)
        assert overlay not in app.screen_stack

