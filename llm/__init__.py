"""Local LLM utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING
from pathlib import Path

try:  # pragma: no cover - optional dependency
    from .universal_dspy_wrapper_v2 import LoggedFewShotWrapper, is_repo_data_path
except ImportError as exc:  # dspy not installed
    def _missing(name: str, _exc: Exception = exc):
        raise ImportError(
            "The 'dspy' package is required to use "
            f"{name}; install it via 'pip install dspy-ai'"
        ) from _exc

    class LoggedFewShotWrapper:  # type: ignore[assignment]
        def __init__(self, *args, **kwargs) -> None:
            _missing("LoggedFewShotWrapper")

    def is_repo_data_path(path: str | Path) -> bool:  # type: ignore[assignment]
        _missing("is_repo_data_path")


if TYPE_CHECKING:  # pragma: no cover - for type checkers only
    from .ai_router import get_preferred_models as _get_preferred_models  # noqa: F401


def __getattr__(name: str):
    if name == "get_preferred_models":
        from .ai_router import get_preferred_models as _get_preferred_models

        return _get_preferred_models
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["LoggedFewShotWrapper", "is_repo_data_path", "get_preferred_models"]

