from __future__ import annotations

import subprocess
from typing import Any, cast, TYPE_CHECKING

from .. import register_backend
from ..base import Backend

if TYPE_CHECKING:  # pragma: no cover - help type checkers
    from .ollama_dspy import OllamaDSPyBackend as _OllamaDSPyBackend  # noqa: F401

try:  # pragma: no cover - optional dependency
    from .ollama_dspy import OllamaDSPyBackend as _ImportedDSPyBackend
except Exception:  # pragma: no cover - optional dependency missing
    _ImportedDSPyBackend = None

OllamaDSPyBackend: type[Backend] | None
OllamaDSPyBackend = _ImportedDSPyBackend


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


def run_ollama(prompt: str, model: str | None) -> str:
    """Return Ollama response for ``prompt`` using ``model``."""

    backend_cls = OllamaDSPyBackend if OllamaDSPyBackend is not None else OllamaBackend
    backend = cast(Any, backend_cls)(model)
    return backend.run(prompt)


register_backend("ollama", run_ollama)


__all__ = ["OllamaBackend", "run_ollama"]
