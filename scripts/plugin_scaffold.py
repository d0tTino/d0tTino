#!/usr/bin/env python3
"""Scaffold a minimal plug-in package.

Generates either a backend or recipe plug-in with entry points for both the
LLM plug-in system and the ``d0ttino.tools`` MCP adapter.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def scaffold_plugin(
    name: str,
    *,
    recipe: bool = False,
    description: str = "A d0tTino plug-in",
    output: str | Path = ".",
) -> Path:
    """Create plug-in template for ``name`` and return the project path."""
    suffix = "recipe" if recipe else "plugin"
    dist_name = f"d0ttino-{name}-{suffix}"
    package = f"d0ttino_{name}_{suffix}"
    root = Path(output).expanduser().resolve() / dist_name
    pkg_dir = root / package
    pkg_dir.mkdir(parents=True, exist_ok=True)

    if recipe:
        init = f'''"""{description}"""
from typing import Dict, List
from llm.backends.plugin_sdk import register_recipe


def run(goal: str):
    """Return shell commands for the given goal."""
    return [f"echo {{goal}}"]


def mcp_tool() -> Dict[str, object]:
    """Return MCP tool metadata."""
    return {{
        "server_url": "https://example.com/mcp",
        "capabilities": ["echo"],
    }}


register_recipe("{name}", run)

__all__: List[str] = ["run", "mcp_tool"]
'''
        entry_group = "d0ttino.recipes"
        entry_line = f'{name} = "{package}:run"'
    else:
        init = f'''"""{description}"""
from typing import Dict, List
from llm.backends.plugin_sdk import register_backend


def run(prompt: str, model: str | None = None) -> str:
    """Generate a completion for the given prompt."""
    return "response"


def mcp_tool() -> Dict[str, object]:
    """Return MCP tool metadata."""
    return {{
        "server_url": "https://example.com/mcp",
        "capabilities": ["echo"],
    }}


register_backend("{name}", run)

__all__: List[str] = ["run", "mcp_tool"]
'''
        entry_group = "llm.plugins"
        entry_line = f'{name} = "{package}"'

    (pkg_dir / "__init__.py").write_text(init, encoding="utf-8")

    pyproject = f'''[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "{dist_name}"
version = "0.1.0"
dependencies = ["llm"]

[project.entry-points."{entry_group}"]
{entry_line}

[project.entry-points."d0ttino.tools"]
{name} = "{package}:mcp_tool"
'''
    (root / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    (root / "mcp.json").write_text(
        json.dumps({"name": name, "version": "0.1.0"}, indent=2),
        encoding="utf-8",
    )
    return root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="Plug-in name")
    parser.add_argument("--output", default=".", help="Destination directory")
    parser.add_argument("--description", default="A d0tTino plug-in")
    parser.add_argument(
        "--recipe", action="store_true", help="Create a recipe plug-in template"
    )
    return parser


def main(argv: list[str] | None = None) -> Path:
    args = build_parser().parse_args(argv)
    return scaffold_plugin(
        args.name,
        recipe=args.recipe,
        description=args.description,
        output=args.output,
    )


if __name__ == "__main__":
    main()
