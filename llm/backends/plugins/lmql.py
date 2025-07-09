from __future__ import annotations

from typing import Any, cast

from ..plugin_sdk import Backend, register_backend

LMQLBackend: type[Backend] | None = None

try:  # pragma: no cover - optional dependency
    import lmql  # noqa: F401
except ImportError:  # pragma: no cover - missing optional dep
    lmql = None


if lmql is not None:
    class _RealLMQLBackend(Backend):
        """Backend implemented using `lmql`."""

        def __init__(self, model: str) -> None:
            self.model = model

        def run(self, prompt: str) -> str:  # pragma: no cover - network placeholder
            return f"lmql:{prompt}:{self.model}"
    LMQLBackend = _RealLMQLBackend
else:  # pragma: no cover - optional dependency missing
    LMQLBackend = None



def run_lmql(prompt: str, model: str) -> str:
    """Return response using ``lmql`` backend."""

    backend = cast(Any, LMQLBackend)(model)
    return backend.run(prompt)


if LMQLBackend is not None:
    register_backend("lmql", run_lmql)


__all__ = ["LMQLBackend", "run_lmql"]
