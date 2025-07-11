"""Utility for discovering entry point plugins."""

from __future__ import annotations

import importlib.metadata
from importlib.metadata import EntryPoint
from collections.abc import Iterator

__all__ = ["discover_entry_points"]


def discover_entry_points(group: str) -> Iterator[EntryPoint]:
    """Yield entry points from ``group`` supporting multiple Python versions."""
    eps = importlib.metadata.entry_points()
    if hasattr(eps, "select"):
        yield from eps.select(group=group)
    elif isinstance(eps, dict):
        yield from eps.get(group, ())
    else:
        for ep in eps:
            if getattr(ep, "group", None) == group:
                yield ep
