from __future__ import annotations

from .base import Backend

try:  # pragma: no cover - optional dependency
    import lmql  # noqa: F401
except ImportError as exc:  # pragma: no cover - missing optional dep
    raise ImportError(
        "The 'lmql' package is required for LMQLBackend"
    ) from exc


class LMQLBackend(Backend):
    """Backend implemented using `lmql`."""

    def __init__(self, model: str) -> None:
        self.model = model

    def run(self, prompt: str) -> str:  # pragma: no cover - network placeholder
        return f"lmql:{prompt}:{self.model}"
