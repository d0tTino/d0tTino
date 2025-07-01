"""Local LLM utilities."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

LoggedFewShotWrapperType: type[Any] | None
is_repo_data_path_fn: Callable[[str | Path], bool] | None

try:  # pragma: no cover - optional dependency
    from .universal_dspy_wrapper_v2 import (
        LoggedFewShotWrapper as LoggedFewShotWrapperType,
        is_repo_data_path as is_repo_data_path_fn,
    )
except ImportError:  # dspy not installed
    LoggedFewShotWrapperType = None
    is_repo_data_path_fn = None

LoggedFewShotWrapper: type[Any] | None = LoggedFewShotWrapperType
is_repo_data_path: Callable[[str | Path], bool] | None = is_repo_data_path_fn

if TYPE_CHECKING:  # pragma: no cover - for type checkers only
    from .ai_router import get_preferred_models as _get_preferred_models  # noqa: F401


def __getattr__(name: str):
    if name == "get_preferred_models":
        from .ai_router import get_preferred_models as _get_preferred_models

        return _get_preferred_models
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    name
    for name in ["LoggedFewShotWrapper", "is_repo_data_path", "get_preferred_models"]
    if name == "get_preferred_models" or locals().get(name) is not None
]

