"""Utility helpers for the llm package."""

from __future__ import annotations

from pathlib import Path
import subprocess
import warnings
from functools import lru_cache


@lru_cache(maxsize=1)
def get_repo_root() -> Path:
    """Return the repository root or ``Path.cwd()`` if detection fails."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True,
        )
        return Path(out.strip())
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:  # pragma: no cover - fall back
        warnings.warn(
            f"Git repo root detection failed: {exc}. Falling back to current working directory.",
            RuntimeWarning,
        )
        return Path.cwd()


__all__ = ["get_repo_root"]
