"""Recipe plug-in loader."""

from __future__ import annotations

import importlib
import importlib.metadata
import pkgutil
from collections.abc import Callable
from typing import Dict, List

RECIPE_ENTRYPOINT_GROUP = "d0ttino.recipes"

Recipe = Callable[[str], List[str]]

__all__ = ["Recipe", "RECIPE_ENTRYPOINT_GROUP", "discover_recipes"]


def discover_recipes() -> Dict[str, Recipe]:
    """Return mapping of recipe names to callables."""

    package = f"{__name__}.plugins"
    recipes: Dict[str, Recipe] = {}
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
            recipes[mod.name] = func

    for entry in importlib.metadata.entry_points().select(group=RECIPE_ENTRYPOINT_GROUP):
        try:
            func = entry.load()
        except Exception:  # pragma: no cover - optional dependency missing
            continue
        if callable(func):
            recipes[entry.name] = func

    return recipes
