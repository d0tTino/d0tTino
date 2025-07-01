"""LLM routing utilities that respect user preferences."""

from __future__ import annotations

import json
import os
import warnings
from pathlib import Path
from typing import Any, Optional, Tuple

from .utils import get_repo_root



_DEFAULT_CONFIG = get_repo_root() / "llm" / "llm_config.json"


def _load_config(path: Path) -> dict[str, Any]:
    """Return configuration loaded from ``path`` if it exists, else empty dict."""
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:  # pragma: no cover - config should be valid
        warnings.warn(f"Failed to parse {path}: {exc}", RuntimeWarning)
        return {}


def get_preferred_models(
    default_primary: str,
    default_fallback: Optional[str] = None,
    *,
    config_path: Optional[Path] = None,
) -> Tuple[str, Optional[str]]:
    """Return primary and fallback model names using optional ``config_path`` or ``LLM_CONFIG_PATH`` env var."""
    env_path = os.environ.get("LLM_CONFIG_PATH")
    if config_path is not None:
        path = config_path
    elif env_path:
        path = Path(env_path)
    else:
        path = _DEFAULT_CONFIG
    cfg = _load_config(path)
    primary = cfg.get("primary_model", default_primary)
    fallback = cfg.get("fallback_model", default_fallback)
    return primary, fallback


__all__ = ["get_preferred_models"]
