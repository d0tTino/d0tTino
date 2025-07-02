"""LLM routing utilities."""

from __future__ import annotations

import os
import subprocess
from typing import List

from .backends import (
    GeminiBackend,
    GeminiDSPyBackend,
    OllamaBackend,
    OllamaDSPyBackend,
    OpenRouterBackend,
    OpenRouterDSPyBackend,
)
from .ai_router import get_preferred_models

DEFAULT_MODEL = "llama3"
DEFAULT_PRIMARY_BACKEND = "gemini"
DEFAULT_FALLBACK_BACKEND = "ollama"

DEFAULT_COMPLEXITY_THRESHOLD = 50


def estimate_prompt_complexity(prompt: str) -> int:
    """Return a basic complexity score for ``prompt``."""
    return len(prompt.split())


def run_gemini(prompt: str, model: str | None = None) -> str:
    """Return Gemini response for ``prompt``."""
    backend_cls = GeminiDSPyBackend if GeminiDSPyBackend is not None else GeminiBackend
    backend = backend_cls(model)  # type: ignore[arg-type]
    return backend.run(prompt)


def run_ollama(prompt: str, model: str) -> str:
    """Return Ollama response for ``prompt`` using ``model``."""
    backend_cls = OllamaDSPyBackend if OllamaDSPyBackend is not None else OllamaBackend
    backend = backend_cls(model)  # type: ignore[arg-type]
    return backend.run(prompt)


def run_openrouter(prompt: str, model: str) -> str:
    """Return OpenRouter response for ``prompt`` using ``model``."""
    backend_cls = (
        OpenRouterDSPyBackend if OpenRouterDSPyBackend is not None else OpenRouterBackend
    )
    backend = backend_cls(model)  # type: ignore[arg-type]
    return backend.run(prompt)


def _preferred_backends() -> tuple[str, str | None]:
    env_primary = os.environ.get("LLM_PRIMARY_BACKEND")
    env_fallback = os.environ.get("LLM_FALLBACK_BACKEND")
    if env_primary:
        return env_primary, env_fallback
    return get_preferred_models(DEFAULT_PRIMARY_BACKEND, DEFAULT_FALLBACK_BACKEND)


def _run_backend(name: str, prompt: str, model: str) -> str:
    name = name.lower()
    if name == "gemini":
        return run_gemini(prompt, model)
    if name == "ollama":
        return run_ollama(prompt, model)
    if name == "openrouter":
        return run_openrouter(prompt, model)
    raise ValueError(f"Unknown backend: {name}")


def send_prompt(prompt: str, *, local: bool = False, model: str = DEFAULT_MODEL) -> str:
    """Send ``prompt`` using the configured backends."""
    primary, fallback = _preferred_backends()
    order: List[str] = []

    env_mode = os.environ.get("LLM_ROUTING_MODE", "auto").lower()
    if local or env_mode == "local":
        if fallback:
            order.append(fallback)
    else:
        if env_mode == "remote":
            order.append(primary)
            if fallback:
                order.append(fallback)
        else:  # auto
            threshold_str = os.environ.get("LLM_COMPLEXITY_THRESHOLD")
            try:
                threshold = int(threshold_str) if threshold_str else DEFAULT_COMPLEXITY_THRESHOLD
            except ValueError:  # pragma: no cover - invalid env value
                threshold = DEFAULT_COMPLEXITY_THRESHOLD
            complexity = estimate_prompt_complexity(prompt)
            if complexity > threshold:
                order.append(primary)
                if fallback:
                    order.append(fallback)
            else:
                if fallback:
                    order.append(fallback)
                order.append(primary)
    for backend_name in order:
        try:
            return _run_backend(backend_name, prompt, model)
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    raise RuntimeError("Unable to process prompt")


__all__ = [
    "DEFAULT_MODEL",
    "DEFAULT_PRIMARY_BACKEND",
    "DEFAULT_FALLBACK_BACKEND",
    "DEFAULT_COMPLEXITY_THRESHOLD",
    "estimate_prompt_complexity",
    "run_gemini",
    "run_ollama",
    "run_openrouter",
    "send_prompt",
]
