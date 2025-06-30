from __future__ import annotations

from .base import Backend


class OpenRouterBackend(Backend):
    """Placeholder OpenRouter client."""

    def __init__(self, model: str) -> None:
        self.model = model

    def run(self, prompt: str) -> str:  # pragma: no cover - network placeholder
        return f"openrouter:{prompt}:{self.model}"
