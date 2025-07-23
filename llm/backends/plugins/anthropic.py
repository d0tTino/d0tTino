from __future__ import annotations

import os
from typing import Any, Mapping, cast

import requests

from ..plugin_sdk import Backend, register_backend

DEFAULT_BASE_URL = "https://api.anthropic.com/v1"


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


class AnthropicBackend(Backend):
    """HTTP client for the Anthropic API."""

    def __init__(self, model: str) -> None:
        self.model = model
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.base_url = os.environ.get("ANTHROPIC_BASE_URL", DEFAULT_BASE_URL).rstrip("/")

    def run(self, prompt: str) -> str:
        if not self.api_key:  # pragma: no cover - sanity check
            raise RuntimeError("ANTHROPIC_API_KEY is not set")

        url = f"{self.base_url}/messages"
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


def run_anthropic(prompt: str, model: str | None = None) -> str:
    """Return Anthropic response for ``prompt`` using ``model``."""

    backend = cast(Any, AnthropicBackend)(model or "")
    return backend.run(prompt)


register_backend("anthropic", run_anthropic)

__all__ = ["AnthropicBackend", "run_anthropic"]
