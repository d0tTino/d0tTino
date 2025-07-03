"""Backend interfaces and discovery utilities."""

from __future__ import annotations

from collections.abc import Callable
from typing import Dict
import importlib
import pkgutil

from .base import Backend

_BACKEND_REGISTRY: Dict[str, Callable[[str, str], str]] = {}
GeminiDSPyBackend = None
OllamaDSPyBackend = None
OpenRouterDSPyBackend = None
LMQLBackend = None
GuidanceBackend = None
__all__ = [
    "Backend",
    "register_backend",
    "get_backend",
    "clear_registry",
    "discover_plugins",
    "available_backends",
    "GeminiDSPyBackend",
    "OllamaDSPyBackend",
    "OpenRouterDSPyBackend",
    "LMQLBackend",
    "GuidanceBackend",
]


def register_backend(name: str, func: Callable[[str, str], str]) -> None:
    """Register ``func`` to handle ``name``."""
    _BACKEND_REGISTRY[name.lower()] = func


def get_backend(name: str) -> Callable[[str, str], str]:
    """Return the backend callable registered for ``name``."""
    key = name.lower()
    if key not in _BACKEND_REGISTRY:
        raise ValueError(f"Unknown backend: {name}")
    return _BACKEND_REGISTRY[key]


def clear_registry() -> None:
    """Remove all registered backends (tests only)."""
    _BACKEND_REGISTRY.clear()


def available_backends() -> list[str]:
    """Return a list of registered backend names."""

    return sorted(_BACKEND_REGISTRY)


def discover_plugins() -> None:
    """Import backend plugins so they register themselves."""
    package = f"{__name__}.plugins"
    try:
        pkg = importlib.import_module(package)
    except Exception:  # pragma: no cover - plugins package missing
        return
    for mod in pkgutil.iter_modules(pkg.__path__):
        name = f"{package}.{mod.name}"
        try:
            module = importlib.import_module(name)
        except Exception:  # pragma: no cover - optional dependency missing
            continue
        for attr in getattr(module, "__all__", []):
            globals()[attr] = getattr(module, attr)
            if attr not in __all__:
                __all__.append(attr)


# Discover plugins at import time
discover_plugins()
