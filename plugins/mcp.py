"""MCP adapter exposing registered tools."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Dict

from .utils import discover_entry_points

__all__ = ["iter_tools", "get_tools"]


ENTRY_POINT_GROUP = "d0ttino.tools"


def iter_tools() -> Iterator[tuple[str, Any]]:
    """Yield ``(name, tool)`` for each registered MCP tool.

    Tools are discovered from the :data:`ENTRY_POINT_GROUP` entry point
    group. Any entry point that fails to load is skipped.
    """
    for ep in discover_entry_points(ENTRY_POINT_GROUP):
        try:
            yield ep.name, ep.load()
        except Exception:  # pragma: no cover - best effort loading
            continue


def get_tools() -> Dict[str, Any]:
    """Return a mapping of MCP tool names to loaded objects."""
    return {name: tool for name, tool in iter_tools()}
