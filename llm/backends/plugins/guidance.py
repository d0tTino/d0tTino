from __future__ import annotations

from typing import Any, cast

from .. import register_backend
from ..base import Backend

try:  # pragma: no cover - optional dependency
    import guidance  # noqa: F401
except ImportError as exc:  # pragma: no cover - missing optional dep
    raise ImportError(
        "The 'guidance' package is required for GuidanceBackend"
    ) from exc


class GuidanceBackend(Backend):
    """Backend implemented using `guidance`."""

    def __init__(self, model: str) -> None:
        self.model = model

    def run(self, prompt: str) -> str:  # pragma: no cover - network placeholder
        return f"guidance:{prompt}:{self.model}"


def run_guidance(prompt: str, model: str) -> str:
    """Return response using ``guidance`` backend."""

    backend = cast(Any, GuidanceBackend)(model)
    return backend.run(prompt)


register_backend("guidance", run_guidance)


__all__ = ["GuidanceBackend", "run_guidance"]
