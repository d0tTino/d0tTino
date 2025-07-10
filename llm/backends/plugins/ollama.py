from __future__ import annotations

import subprocess
from typing import Any, cast

from ..plugin_sdk import Backend, register_backend

OllamaDSPyBackend: type[Backend] | None
try:  # pragma: no cover - optional dependency
    from .ollama_dspy import OllamaDSPyBackend as OllamaDSPyBackend
except Exception:  # pragma: no cover - optional dependency missing
    OllamaDSPyBackend = None



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


def run_ollama(prompt: str, model: str | None = None) -> str:
    """Return Ollama response for ``prompt`` using ``model``."""

    backend_cls = OllamaDSPyBackend if OllamaDSPyBackend is not None else OllamaBackend
    backend = cast(Any, backend_cls)(model or "")
    return backend.run(prompt)


register_backend("ollama", run_ollama)


__all__ = ["OllamaBackend", "run_ollama"]
