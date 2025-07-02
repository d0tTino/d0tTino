from __future__ import annotations

from .base import Backend

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
