from .base import Backend
from .gemini import GeminiBackend
from .ollama import OllamaBackend
from .openrouter import OpenRouterBackend
from ..langchain_backend import LangChainBackend

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
]
