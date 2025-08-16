"""Example MCP plugin providing metadata for tests."""

from __future__ import annotations

from typing import Dict, List


def mcp_tool() -> Dict[str, object]:
    """Return example MCP metadata."""
    return {
        "server_url": "https://example.com/mcp",
        "capabilities": ["echo"],
    }


__all__: List[str] = ["mcp_tool"]
