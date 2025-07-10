from __future__ import annotations

import os
from typing import Any, Mapping, cast

import requests

from ..plugin_sdk import Backend, register_backend

OpenRouterDSPyBackend: type[Backend] | None
try:  # pragma: no cover - optional dependency
    from .openrouter_dspy import OpenRouterDSPyBackend as OpenRouterDSPyBackend
except Exception:  # pragma: no cover - optional dependency missing
    OpenRouterDSPyBackend = None



DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


def _extract_text(result: Mapping[str, Any]) -> str:
    """Return the assistant text from a LiteLLM-style result."""
    try:
        choices = result["choices"]
        first = choices[0]
        if isinstance(first, dict):
            if "message" in first:
                return first["message"].get("content", "")
            return first.get("text", "")
    except Exception:  # pragma: no cover - fall back to str()
        pass
    return str(result)


class OpenRouterBackend(Backend):
    """HTTP client for the OpenRouter API."""

    def __init__(self, model: str) -> None:
        self.model = model
        self.api_key = os.environ.get("OPENROUTER_API_KEY")
        self.base_url = os.environ.get("OPENROUTER_BASE_URL", DEFAULT_BASE_URL).rstrip("/")

    def run(self, prompt: str) -> str:
        if not self.api_key:  # pragma: no cover - sanity check
            raise RuntimeError("OPENROUTER_API_KEY is not set")

        url = f"{self.base_url}/chat/completions"
        response = requests.post(
            url,
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
            },
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return _extract_text(data)


def run_openrouter(prompt: str, model: str | None = None) -> str:
    """Return OpenRouter response for ``prompt`` using ``model``."""

    backend_cls = (
        OpenRouterDSPyBackend if OpenRouterDSPyBackend is not None else OpenRouterBackend
    )
    backend = cast(Any, backend_cls)(model or "")
    return backend.run(prompt)


register_backend("openrouter", run_openrouter)


__all__ = ["OpenRouterBackend", "run_openrouter"]
