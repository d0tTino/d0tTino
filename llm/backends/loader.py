from __future__ import annotations

import importlib
from plugins.discovery import iter_entry_points
import pkgutil

import llm.backends as backends

__all__ = ["discover_plugins", "load_backends"]


def discover_plugins() -> None:
    """Import backend plugins so they register themselves."""
    package = f"{backends.__name__}.plugins"
    paths: list[str] = []
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
        for attr in getattr(module, "__all__", []):
            setattr(backends, attr, getattr(module, attr))
            if attr not in backends.__all__:
                backends.__all__.append(attr)

    for entry in iter_entry_points("llm.plugins"):
        try:
            module = entry.load()
        except Exception:  # pragma: no cover - optional dependency missing
            continue
        for attr in getattr(module, "__all__", []):
            setattr(backends, attr, getattr(module, attr))
            if attr not in backends.__all__:
                backends.__all__.append(attr)


def load_backends() -> None:
    """Convenience wrapper to import all available backends."""
    discover_plugins()
