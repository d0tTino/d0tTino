"""SDK for writing llm and recipe plug-ins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Dict, List

from . import register_backend as _register_backend
from .base import Backend

BACKEND_ENTRYPOINT_GROUP = "llm.plugins"
RECIPE_ENTRYPOINT_GROUP = "d0ttino.recipes"

RecipeCallable = Callable[[str], List[str]]

_RECIPE_REGISTRY: Dict[str, RecipeCallable] = {}


class Recipe(ABC):
    """Base class for automation recipes."""

    @abstractmethod
    def run(self, goal: str) -> List[str]:
        """Return shell commands for ``goal``."""
        raise NotImplementedError


def register_backend(name: str, func: Callable[[str, str | None], str]) -> None:
    """Register ``func`` under ``name`` for backend routing."""
    _register_backend(name, func)


def register_recipe(name: str, func: RecipeCallable) -> None:
    """Register ``func`` under ``name`` for recipe discovery."""
    _RECIPE_REGISTRY[name] = func


def get_registered_recipes() -> Dict[str, RecipeCallable]:
    """Return all recipes registered via :func:`register_recipe`."""
    return dict(_RECIPE_REGISTRY)


__all__ = [
    "Backend",
    "Recipe",
    "BACKEND_ENTRYPOINT_GROUP",
    "RECIPE_ENTRYPOINT_GROUP",
    "register_backend",
    "register_recipe",
    "get_registered_recipes",
]
