from .base import Backend
from .gemini import GeminiBackend
from .ollama import OllamaBackend
from .openrouter import OpenRouterBackend

try:  # pragma: no cover - optional dependency
    from .dspy_backends import (
        GeminiDSPyBackend,
        OllamaDSPyBackend,
        OpenRouterDSPyBackend,
    )
except Exception:  # pragma: no cover - dspy missing
    GeminiDSPyBackend = None
    OllamaDSPyBackend = None
    OpenRouterDSPyBackend = None

__all__ = [
    "Backend",
    "GeminiBackend",
    "OllamaBackend",
    "OpenRouterBackend",
    "GeminiDSPyBackend",
    "OllamaDSPyBackend",
    "OpenRouterDSPyBackend",
]
