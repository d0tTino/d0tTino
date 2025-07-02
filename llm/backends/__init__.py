from collections.abc import Callable
from typing import Dict

from .base import Backend
from .gemini import GeminiBackend
from .ollama import OllamaBackend
from .openrouter import OpenRouterBackend
from ..langchain_backend import LangChainBackend

_BACKEND_REGISTRY: Dict[str, Callable[[str, str], str]] = {}


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

GeminiDSPyBackendType: type[Backend] | None
OllamaDSPyBackendType: type[Backend] | None
OpenRouterDSPyBackendType: type[Backend] | None

try:  # pragma: no cover - optional dependency
    from .dspy_backends import (
        GeminiDSPyBackend as GeminiDSPyBackendType,
        OllamaDSPyBackend as OllamaDSPyBackendType,
        OpenRouterDSPyBackend as OpenRouterDSPyBackendType,
    )
except Exception:  # pragma: no cover - dspy missing
    GeminiDSPyBackendType = None
    OllamaDSPyBackendType = None
    OpenRouterDSPyBackendType = None

GeminiDSPyBackend: type[Backend] | None = GeminiDSPyBackendType
OllamaDSPyBackend: type[Backend] | None = OllamaDSPyBackendType
OpenRouterDSPyBackend: type[Backend] | None = OpenRouterDSPyBackendType

__all__ = [
    "Backend",
    "GeminiBackend",
    "OllamaBackend",
    "OpenRouterBackend",
    "LangChainBackend",
    "GeminiDSPyBackend",
    "OllamaDSPyBackend",
    "OpenRouterDSPyBackend",
    "register_backend",
    "get_backend",
    "clear_registry",
]
