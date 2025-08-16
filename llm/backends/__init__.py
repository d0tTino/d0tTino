"""Backend interfaces and discovery utilities."""

from __future__ import annotations

from collections.abc import Callable
from typing import Dict

from .loader import discover_plugins, load_backends
from .base import Backend
from .superclaude import SuperClaudeBackend as _RealSuperClaudeBackend

_INITIALIZED = False


_BACKEND_REGISTRY: Dict[str, Callable[[str, str], str]] = {}
GeminiBackend: type[Backend] | None = None
OllamaBackend: type[Backend] | None = None
OpenRouterBackend: type[Backend] | None = None
LobeChatBackend: type[Backend] | None = None
MindBridgeBackend: type[Backend] | None = None
AnthropicBackend: type[Backend] | None = None
MistralBackend: type[Backend] | None = None
SuperClaudeBackend: type[Backend] | None = _RealSuperClaudeBackend  # noqa: F811

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
    "load_backends",
    "available_backends",
    "GeminiBackend",
    "OllamaBackend",
    "OpenRouterBackend",
    "LobeChatBackend",
    "MindBridgeBackend",
    "AnthropicBackend",
    "MistralBackend",
    "SuperClaudeBackend",
    "GeminiDSPyBackend",
    "OllamaDSPyBackend",
    "OpenRouterDSPyBackend",
    "LMQLBackend",
    "GuidanceBackend",
    "initialize",
]


def register_backend(name: str, func: Callable[[str, str], str]) -> None:
    """Register ``func`` to handle ``name`` and mirror to ``ai_router``."""
    _BACKEND_REGISTRY[name.lower()] = func
    try:  # pragma: no cover - tests may not import ai_router
        from llm import ai_router as _ai_router
        attr = f"run_{name.lower()}"
        if hasattr(_ai_router, attr):
            setattr(_ai_router, attr, func)
    except Exception:
        pass


def get_backend(name: str) -> Callable[[str, str], str]:
    """Return the backend callable registered for ``name``."""
    key = name.lower()
    if key == "superclaude":
        from llm import router as _router
        return _router.run_superclaude
    if key not in _BACKEND_REGISTRY:
        raise ValueError(f"Unknown backend: {name}")
    return _BACKEND_REGISTRY[key]


def clear_registry() -> None:
    """Remove all registered backends (tests only)."""
    _BACKEND_REGISTRY.clear()


def available_backends() -> list[str]:
    """Return a list of registered backend names."""

    return sorted(_BACKEND_REGISTRY)


def initialize() -> None:
    """Load backends once and cache the result."""
    global _INITIALIZED
    if not _INITIALIZED:
        load_backends()
        _INITIALIZED = True



