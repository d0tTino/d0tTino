from __future__ import annotations

from typing import Any, cast, TYPE_CHECKING

from .. import register_backend
from ..base import Backend

if TYPE_CHECKING:  # pragma: no cover - help type checkers
    from .openrouter_dspy import OpenRouterDSPyBackend as _OpenRouterDSPyBackend  # noqa: F401

try:  # pragma: no cover - optional dependency
    from .openrouter_dspy import OpenRouterDSPyBackend as _ImportedDSPyBackend
except Exception:  # pragma: no cover - optional dependency missing
    _ImportedDSPyBackend = None

OpenRouterDSPyBackend: type[Backend] | None
OpenRouterDSPyBackend = _ImportedDSPyBackend


class OpenRouterBackend(Backend):
    """Placeholder OpenRouter client."""

    def __init__(self, model: str) -> None:
        self.model = model

    def run(self, prompt: str) -> str:  # pragma: no cover - network placeholder
        return f"openrouter:{prompt}:{self.model}"


def run_openrouter(prompt: str, model: str | None) -> str:
    """Return OpenRouter response for ``prompt`` using ``model``."""

    backend_cls = (
        OpenRouterDSPyBackend if OpenRouterDSPyBackend is not None else OpenRouterBackend
    )
    backend = cast(Any, backend_cls)(model)
    return backend.run(prompt)


register_backend("openrouter", run_openrouter)


__all__ = ["OpenRouterBackend", "run_openrouter"]
