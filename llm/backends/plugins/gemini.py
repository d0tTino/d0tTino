from __future__ import annotations

import subprocess

from typing import Any, cast, TYPE_CHECKING

from .. import register_backend
from ..base import Backend

if TYPE_CHECKING:  # pragma: no cover - help type checkers
    from .gemini_dspy import GeminiDSPyBackend as _GeminiDSPyBackend  # noqa: F401

try:  # pragma: no cover - optional dependency
    from .gemini_dspy import GeminiDSPyBackend as _ImportedDSPyBackend
except Exception:  # pragma: no cover - optional dependency missing
    _ImportedDSPyBackend = None

GeminiDSPyBackend: type[Backend] | None
GeminiDSPyBackend = _ImportedDSPyBackend


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


def run_gemini(prompt: str, model: str | None = None) -> str:
    """Return Gemini response for ``prompt``."""

    backend_cls = GeminiDSPyBackend if GeminiDSPyBackend is not None else GeminiBackend
    backend = cast(Any, backend_cls)(model)
    return backend.run(prompt)


register_backend("gemini", run_gemini)


__all__ = ["GeminiBackend", "run_gemini"]
