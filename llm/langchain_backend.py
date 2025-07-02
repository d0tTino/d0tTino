from __future__ import annotations

from typing import Any

from .backends.base import Backend


class LangChainBackend(Backend):
    """Backend that delegates to a LangChain chain."""

    def __init__(self, chain: Any) -> None:
        self.chain = chain

    def run(self, prompt: str) -> str:
        try:
            result = self.chain.invoke({"input": prompt})
        except Exception:
            result = self.chain.invoke(prompt)
        if isinstance(result, dict):
            result = result.get("text") or result.get("output") or result
        return str(result)
