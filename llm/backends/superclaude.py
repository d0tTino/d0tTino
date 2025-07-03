from __future__ import annotations

import requests

from .base import Backend


class SuperClaudeBackend(Backend):
    """HTTP client for the fictional SuperClaude service."""

    def __init__(self, model: str) -> None:
        self.model = model

    def run(self, prompt: str) -> str:  # pragma: no cover - network placeholder
        response = requests.post(
            "https://api.superclaude.ai/generate",
            json={"model": self.model, "prompt": prompt},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("text", "")
