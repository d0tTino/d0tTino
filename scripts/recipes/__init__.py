"""Recipe plug-in loader."""

from __future__ import annotations

import importlib
from plugins.utils import discover_entry_points
import pkgutil
from collections.abc import Callable
from typing import Dict, List

from llm.backends.plugin_sdk import (
    RECIPE_ENTRYPOINT_GROUP,
    get_registered_recipes,
    register_recipe,
)

Recipe = Callable[[str], List[str]]

__all__ = ["Recipe", "RECIPE_ENTRYPOINT_GROUP", "register_recipe", "discover_recipes"]


def discover_recipes() -> Dict[str, Recipe]:
    """Return mapping of recipe names to callables."""

    package = f"{__name__}.plugins"
    recipes: Dict[str, Recipe] = get_registered_recipes()
    paths: List[str] = []
    try:
        pkg = importlib.import_module(package)
        paths = list(pkg.__path__)
    except Exception:  # pragma: no cover - plugins package missing
        pass

    for mod in pkgutil.iter_modules(paths):
        name = f"{package}.{mod.name}"
        try:
            module = importlib.import_module(name)
        except Exception:  # pragma: no cover - optional dependency missing
            continue
        func = getattr(module, "run", None)
        if callable(func):
            recipes.setdefault(mod.name, func)

    for entry in discover_entry_points(RECIPE_ENTRYPOINT_GROUP):
        try:
            func = entry.load()
        except Exception:  # pragma: no cover - optional dependency missing
            continue
        if callable(func):
            recipes.setdefault(entry.name, func)

    return recipes
