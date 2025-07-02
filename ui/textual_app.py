from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Input, Button, Static, Select
from textual.containers import Vertical

from llm.router import send_prompt
from scripts.thm import apply_palette, PALETTES_DIR, REPO_ROOT


class TerminalUI(App):
    """Minimal Textual interface for prompt sending and palette application."""

    CSS_PATH = None
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:  # pragma: no cover - simple UI
        palettes = [(p.stem, p.stem) for p in PALETTES_DIR.glob("*.toml")]
        yield Vertical(
            Static("Send Prompt"),
            Input(placeholder="Enter prompt", id="prompt"),
            Button("Send", id="send"),
            Static(id="response"),
            Static("Apply Palette"),
            Select(palettes, id="palette"),
            Button("Apply", id="apply"),
            Static(id="status"),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:  # pragma: no cover
        if event.button.id == "send":
            prompt = self.query_one("#prompt", Input).value
            if prompt:
                result = send_prompt(prompt)
                self.query_one("#response", Static).update(result)
        elif event.button.id == "apply":
            palette = self.query_one("#palette", Select).value
            if palette:
                apply_palette(palette, REPO_ROOT)
                self.query_one("#status", Static).update(f"Applied {palette}")


if __name__ == "__main__":  # pragma: no cover - manual launch
    TerminalUI().run()
