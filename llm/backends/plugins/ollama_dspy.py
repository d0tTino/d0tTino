from __future__ import annotations

from typing import Any, Callable, Mapping

from ..base import Backend

try:  # pragma: no cover - optional dependency
    import dspy
except ImportError:  # pragma: no cover - optional dependency
    dspy = None

_LM: Callable[..., Any] | None = None
LM: Callable[..., Any]
OllamaDSPyBackend: type[Backend] | None
if dspy is not None:
    _LM = getattr(dspy, "LLM", getattr(dspy, "LM", None))
    if _LM is None:  # pragma: no cover - sanity check
        raise ImportError("dspy does not expose an LLM wrapper")
    LM = _LM

    class _OllamaDSPyBackend(Backend):
        """Ollama backend implemented via ``dspy``."""

        def __init__(self, model: str) -> None:
            self.lm = LM(model=model)

        def run(self, prompt: str) -> str:
            result = self.lm.forward(prompt=prompt)
            return _extract_text(result)
    OllamaDSPyBackend = _OllamaDSPyBackend
else:  # pragma: no cover - optional dependency missing
    OllamaDSPyBackend = None


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


__all__ = ["OllamaDSPyBackend"]
