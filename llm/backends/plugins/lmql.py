from __future__ import annotations

from typing import Any, cast

from .. import register_backend
from ..base import Backend

try:  # pragma: no cover - optional dependency
    import lmql  # noqa: F401
except ImportError:  # pragma: no cover - missing optional dep
    lmql = None


if lmql is not None:
    class LMQLBackend(Backend):
        """Backend implemented using `lmql`."""

        def __init__(self, model: str) -> None:
            self.model = model

        def run(self, prompt: str) -> str:  # pragma: no cover - network placeholder
            return f"lmql:{prompt}:{self.model}"
else:  # pragma: no cover - optional dependency missing
    LMQLBackend = None  # type: ignore[misc, assignment]


def run_lmql(prompt: str, model: str) -> str:
    """Return response using ``lmql`` backend."""

    backend = cast(Any, LMQLBackend)(model)
    return backend.run(prompt)


if LMQLBackend is not None:
    register_backend("lmql", run_lmql)


__all__ = ["LMQLBackend", "run_lmql"]
