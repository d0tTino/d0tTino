from __future__ import annotations

import os
from typing import Any, Mapping, cast

import requests

from ..plugin_sdk import Backend, register_backend


DEFAULT_BASE_URL = "http://localhost:3210/api"


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


class LobeChatBackend(Backend):
    """HTTP client for the LobeChat API."""

    def __init__(self, model: str) -> None:
        self.model = model
        self.api_key = os.environ.get("LOBECHAT_API_KEY")
        self.base_url = os.environ.get("LOBECHAT_BASE_URL", DEFAULT_BASE_URL).rstrip("/")

    def run(self, prompt: str) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        response = requests.post(
            url,
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
            },
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return _extract_text(data)


def run_lobechat(prompt: str, model: str | None = None) -> str:
    """Return LobeChat response for ``prompt`` using ``model``."""

    backend = cast(Any, LobeChatBackend)(model or "")
    return backend.run(prompt)


register_backend("lobechat", run_lobechat)

__all__ = ["LobeChatBackend", "run_lobechat"]
