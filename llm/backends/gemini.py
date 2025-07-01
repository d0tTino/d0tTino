from __future__ import annotations

import subprocess

from .base import Backend


class GeminiBackend(Backend):
    """Backend that invokes the ``gemini`` CLI."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model

    def run(self, prompt: str) -> str:
        cmd = ["gemini"]
        if self.model:
            cmd += ["--model", self.model]
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
