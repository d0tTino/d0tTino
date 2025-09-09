"""MCP server wrapper exposing registry-defined tools.

This module converts plug-in registry entries that include ``mcp`` metadata
into callable tools and optionally serves them over a minimal JSON protocol.
Entries can either expose a Python ``entry_point`` or provide remote
``server_url`` details. For the latter a trivial callable returning the
metadata is generated.
"""

from __future__ import annotations

import importlib
import json
import sys
from typing import Any, Dict, Iterator

from scripts import plugins as registry

__all__ = [
    "iter_tools",
    "get_tools",
    "iter_tool_descriptors",
    "get_tool_descriptors",
    "serve",
]


def iter_tools(registry_data: Dict[str, object] | None = None) -> Iterator[tuple[str, Any]]:
    """Yield ``(name, tool)`` for each plug-in exposing MCP metadata.

    ``registry_data`` should be a mapping in the format returned by
    :func:`scripts.plugins.load_registry` when ``raw=True``. When omitted, the
    registry is loaded on demand.
    """

    if registry_data is None:
        registry_data = registry.load_registry(raw=True)

    for name, meta in registry_data.items():
        if not isinstance(meta, dict):
            continue
        mcp_meta = meta.get("mcp")
        if not isinstance(mcp_meta, dict):
            continue
        entry = mcp_meta.get("entry_point")
        if isinstance(entry, str):
            try:
                module_name, obj_name = entry.split(":", 1)
                module = importlib.import_module(module_name)
                yield name, getattr(module, obj_name)
                continue
            except Exception:  # pragma: no cover - best effort loading
                continue
        descriptor = mcp_meta.get("descriptor")
        if isinstance(descriptor, dict):
            desc_copy = descriptor.copy()
            desc_copy.setdefault("name", name)

            def _tool(desc=desc_copy):
                return desc

            yield name, _tool


def get_tools(registry_data: Dict[str, object] | None = None) -> Dict[str, Any]:
    """Return a mapping of tool names to loaded callables."""

    return {name: tool for name, tool in iter_tools(registry_data)}


def iter_tool_descriptors(
    registry_data: Dict[str, object] | None = None,
) -> Iterator[tuple[str, Dict[str, Any]]]:
    """Yield ``(name, descriptor)`` for each MCP-enabled plug-in."""

    for name, tool in iter_tools(registry_data):
        try:
            desc = tool()
        except Exception:  # pragma: no cover - best effort loading
            continue
        if isinstance(desc, dict):
            desc_copy = desc.copy()
            desc_copy.setdefault("name", name)
            yield name, desc_copy


def get_tool_descriptors(
    registry_data: Dict[str, object] | None = None,
) -> Dict[str, Dict[str, Any]]:
    """Return a mapping of tool names to MCP descriptors."""

    return {name: desc for name, desc in iter_tool_descriptors(registry_data)}


def serve(registry_data: Dict[str, object] | None = None) -> None:
    """Serve tools over a line-oriented JSON protocol on ``stdin``/``stdout``.

    Each request should be a JSON object containing ``tool`` and optional
    ``args`` keys. Responses are JSON objects with either ``result`` or
    ``error`` keys.
    """

    tools = get_tools(registry_data)
    descriptors = get_tool_descriptors(registry_data)

    for line in sys.stdin:
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp: Dict[str, Any]
        command = req.get("command")
        if command == "list_tools":
            resp = {"result": list(descriptors.values())}
        else:
            name = req.get("tool")
            args = req.get("args") or {}
            func = tools.get(name)
            if func is None:
                resp = {"error": f"unknown tool: {name}"}
            else:
                try:
                    result = func(**args)
                    resp = {"result": result}
                except Exception as exc:  # pragma: no cover - propagate error
                    resp = {"error": str(exc)}
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()

