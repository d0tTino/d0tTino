from __future__ import annotations

import subprocess

from .base import Backend


class OllamaBackend(Backend):
    """Backend that calls Ollama's ``ollama run`` command."""

    def __init__(self, model: str) -> None:
        self.model = model

    def run(self, prompt: str) -> str:
        cmd = ["ollama", "run", self.model, prompt]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
