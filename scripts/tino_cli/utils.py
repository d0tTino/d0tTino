"""Utility helpers for the CLI bridge."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from telemetry import analytics_default

from .env import _REPO_ROOT
from .models import TelemetryStatus

_CACHE_ROOT = Path.home() / ".cache" / "d0ttino"


def ensure_cache_dir() -> Path:
    """Ensure the cache directory exists and return it."""

    _CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    return _CACHE_ROOT


def python_module_path() -> str:
    """Return the PYTHONPATH root for launching helper modules."""

    return str(_REPO_ROOT)


def telemetry_status() -> TelemetryStatus:
    """Return the current telemetry configuration."""

    enabled = analytics_default()
    endpoint = os.environ.get("EVENTS_URL") if enabled else None
    return TelemetryStatus(enabled=enabled, endpoint=endpoint)


def json_dumps(data: Any) -> str:
    """Serialize ``data`` to a compact JSON string."""

    import json

    return json.dumps(data, separators=(",", ":"))


__all__ = [
    "ensure_cache_dir",
    "json_dumps",
    "python_module_path",
    "telemetry_status",
]
