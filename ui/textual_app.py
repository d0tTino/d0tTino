from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, ProgressBar, Select, Static

from llm.router import send_prompt
from scripts.thm import apply_palette, PALETTES_DIR, REPO_ROOT


class PlanOverlay(ModalScreen[bool]):
    """Overlay that displays planned shell steps and auto-accepts."""

    def __init__(self, steps: list[str], timeout: float = 3) -> None:
        super().__init__()
        self.steps = steps
        self.timeout = timeout
        self._remaining = int(timeout * 10)

    BINDINGS = [("y", "accept", "Accept"), ("n", "decline", "Decline")]

    def compose(self) -> ComposeResult:  # pragma: no cover - simple UI
        yield Static("\n".join(self.steps), id="plan")
        yield ProgressBar(total=self._remaining, id="timer", show_eta=False)

    def on_mount(self) -> None:
        self.set_interval(0.1, self._tick)

    def _tick(self) -> None:
        self._remaining -= 1
        self.query_one("#timer", ProgressBar).advance(1)
        if self._remaining <= 0:
            self.action_accept()

    def action_accept(self) -> None:
        self.dismiss(True)

    def action_decline(self) -> None:
        self.dismiss(False)


class TerminalUI(App):
    """Minimal Textual interface for prompt sending and palette application."""

    CSS_PATH = None
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+p", "command_palette", "Command Palette"),
    ]

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
            if isinstance(palette, str):
                apply_palette(palette, REPO_ROOT)
                self.query_one("#status", Static).update(f"Applied {palette}")

    def show_plan(self, steps: list[str], timeout: float = 3) -> None:
        """Display a plan overlay with an auto-accept timer."""
        self.push_screen(PlanOverlay(steps, timeout))


if __name__ == "__main__":  # pragma: no cover - manual launch
    TerminalUI().run()
