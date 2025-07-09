from __future__ import annotations

import subprocess

from typing import Any, cast

from .. import register_backend
from ..base import Backend

GeminiDSPyBackend: type[Backend] | None
try:  # pragma: no cover - optional dependency
    from .gemini_dspy import GeminiDSPyBackend as GeminiDSPyBackend
except Exception:  # pragma: no cover - optional dependency missing
    GeminiDSPyBackend = None


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

    if GeminiDSPyBackend is not None:
        backend = cast(Any, GeminiDSPyBackend)(model)
        try:
            return backend.run(prompt)
        except Exception:
            pass

    backend = GeminiBackend(model)
    return backend.run(prompt)


register_backend("gemini", run_gemini)


__all__ = ["GeminiBackend", "run_gemini"]
