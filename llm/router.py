"""LLM routing utilities."""

from __future__ import annotations

import os
import subprocess
from typing import Any, List, cast

from .backends import (
    GeminiBackend,
    GeminiDSPyBackend,
    OllamaBackend,
    OllamaDSPyBackend,
    OpenRouterBackend,
    OpenRouterDSPyBackend,
    register_backend,
    get_backend,
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
    backend_cls = (
        GeminiDSPyBackend if GeminiDSPyBackend is not None else GeminiBackend
    )
    backend = cast(Any, backend_cls)(model)
    return backend.run(prompt)


register_backend("gemini", run_gemini)


def run_ollama(prompt: str, model: str) -> str:
    """Return Ollama response for ``prompt`` using ``model``."""
    backend_cls = (
        OllamaDSPyBackend if OllamaDSPyBackend is not None else OllamaBackend
    )
    backend = cast(Any, backend_cls)(model)
    return backend.run(prompt)


register_backend("ollama", run_ollama)


def run_openrouter(prompt: str, model: str) -> str:
    """Return OpenRouter response for ``prompt`` using ``model``."""
    backend_cls = (
        OpenRouterDSPyBackend if OpenRouterDSPyBackend is not None else OpenRouterBackend
    )
    backend = cast(Any, backend_cls)(model)
    return backend.run(prompt)


register_backend("openrouter", run_openrouter)


def _preferred_backends() -> tuple[str, str | None]:
    env_primary = os.environ.get("LLM_PRIMARY_BACKEND")
    env_fallback = os.environ.get("LLM_FALLBACK_BACKEND")
    if env_primary:
        return env_primary, env_fallback
    return get_preferred_models(DEFAULT_PRIMARY_BACKEND, DEFAULT_FALLBACK_BACKEND)


def _run_backend(name: str, prompt: str, model: str) -> str:
    """Run ``name`` backend with ``prompt`` and ``model``.

    Prefer dynamically patched ``run_<name>`` functions if present so tests can
    monkeypatch the module without re-registering backends. Fall back to the
    backend registry otherwise.
    """
    attr = globals().get(f"run_{name.lower()}")
    if callable(attr):
        return attr(prompt, model)
    func = get_backend(name)
    return func(prompt, model)


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
