"""Integration tests for the plug-in scaffold utility."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

from llm.backends import available_backends, clear_registry
from llm.backends.plugin_sdk import get_registered_recipes
from scripts import plugin_scaffold


def _import_plugin(path: Path, module: str) -> None:
    sys.path.insert(0, str(path))
    importlib.import_module(module)
    sys.path.pop(0)


def test_scaffold_backend_registers(tmp_path: Path) -> None:
    project = plugin_scaffold.scaffold_plugin("demo", output=tmp_path)
    clear_registry()
    _import_plugin(project, "d0ttino_demo_plugin")
    assert "demo" in available_backends()


def test_scaffold_recipe_registers(tmp_path: Path) -> None:
    project = plugin_scaffold.scaffold_plugin("demo", output=tmp_path, recipe=True)
    _import_plugin(project, "d0ttino_demo_recipe")
    assert "demo" in get_registered_recipes()
