"""MCP adapter exposing registered tools.

Enabled tools are loaded from ``~/.config/d0tTino/mcp.json`` and merged with
those discovered via the ``d0ttino.tools`` entry point group.
"""

from __future__ import annotations

import json
from pathlib import Path
from collections.abc import Iterator
from typing import Any, Dict

from .utils import discover_entry_points

__all__ = ["iter_tools", "get_tools"]


ENTRY_POINT_GROUP = "d0ttino.tools"
CONFIG_PATH = Path.home() / ".config" / "d0tTino" / "mcp.json"


def iter_tools() -> Iterator[tuple[str, Any]]:
    """Yield ``(name, tool)`` for each registered MCP tool.

    Tools are discovered from the :data:`ENTRY_POINT_GROUP` entry point group.
    Any entry point that fails to load is skipped.
    """
    for ep in discover_entry_points(ENTRY_POINT_GROUP):
        try:
            yield ep.name, ep.load()
        except Exception:  # pragma: no cover - best effort loading
            continue


def _load_config() -> Dict[str, Any]:
    try:
        data = json.loads(CONFIG_PATH.read_text())
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def get_tools() -> Dict[str, Any]:
    """Return a mapping of MCP tool names to loaded objects."""
    tools = _load_config()
    for name, func in iter_tools():
        try:
            tools[name] = func()
        except Exception:  # pragma: no cover - best effort loading
            continue
    return tools
