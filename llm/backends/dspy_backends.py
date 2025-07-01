from __future__ import annotations

from .base import Backend

try:  # pragma: no cover - optional dependency
    import dspy
except ImportError as exc:  # pragma: no cover - optional dependency
    raise ImportError(
        "The 'dspy' package is required for DSPy-backed backends"
    ) from exc

_LM = getattr(dspy, "LLM", getattr(dspy, "LM", None))
if _LM is None:  # pragma: no cover - sanity check
    raise ImportError("dspy does not expose an LLM wrapper")


def _extract_text(result: object) -> str:
    """Return the assistant text from a LiteLLM-style result."""
    try:
        choices = result["choices"]  # type: ignore[index]
        first = choices[0]
        if isinstance(first, dict):
            if "message" in first:
                return first["message"].get("content", "")  # type: ignore[index]
            return first.get("text", "")  # type: ignore[return-value]
    except Exception:  # pragma: no cover - fall back to str()
        pass
    return str(result)


class GeminiDSPyBackend(Backend):
    """Gemini backend implemented via ``dspy``."""

    def __init__(self, model: str | None = None) -> None:
        self.lm = _LM(model=model or "google/gemini-pro")

    def run(self, prompt: str) -> str:
        result = self.lm.forward(prompt=prompt)
        return _extract_text(result)


class OllamaDSPyBackend(Backend):
    """Ollama backend implemented via ``dspy``."""

    def __init__(self, model: str) -> None:
        self.lm = _LM(model=model)

    def run(self, prompt: str) -> str:
        result = self.lm.forward(prompt=prompt)
        return _extract_text(result)


class OpenRouterDSPyBackend(Backend):
    """OpenRouter backend implemented via ``dspy``."""

    def __init__(self, model: str) -> None:
        self.lm = _LM(model=model)

    def run(self, prompt: str) -> str:
        result = self.lm.forward(prompt=prompt)
        return _extract_text(result)
