"""LLM routing utilities."""

from __future__ import annotations

import os
import json
import subprocess
from pathlib import Path
from typing import Any, List, Mapping

from .backends import (
    GeminiBackend,  # noqa: F401 - re-exported for tests
    GeminiDSPyBackend,  # noqa: F401 - re-exported for tests
    OllamaBackend,  # noqa: F401 - re-exported for tests
    OllamaDSPyBackend,  # noqa: F401 - re-exported for tests
    OpenRouterBackend,  # noqa: F401 - re-exported for tests
    OpenRouterDSPyBackend,  # noqa: F401 - re-exported for tests
    register_backend,
    get_backend,
)
from .backends.superclaude import SuperClaudeBackend
from .ai_router import get_preferred_models
from .utils import get_repo_root
from .langchain_backend import LangChainBackend

DEFAULT_MODEL = "llama3"
DEFAULT_PRIMARY_BACKEND = "gemini"
DEFAULT_FALLBACK_BACKEND = "ollama"

DEFAULT_COMPLEXITY_THRESHOLD = 50

# Configuration file storing model metadata
_DEFAULT_CONFIG = get_repo_root() / "llm" / "llm_config.json"


def estimate_prompt_complexity(prompt: str) -> int:
    """Return a basic complexity score for ``prompt``."""
    return len(prompt.split())


def run_gemini(prompt: str, model: str | None = None) -> str:
    """Return Gemini response for ``prompt`` using registered backend."""

    func = get_backend("gemini")
    return func(prompt, model)  # type: ignore[arg-type]


def run_ollama(prompt: str, model: str) -> str:
    """Return Ollama response for ``prompt`` using ``model`` and registered backend."""

    func = get_backend("ollama")
    return func(prompt, model)


def run_openrouter(prompt: str, model: str) -> str:
    """Return OpenRouter response for ``prompt`` using ``model`` and registered backend."""

    func = get_backend("openrouter")
    return func(prompt, model)


def _load_model_data(path: Path) -> Mapping[str, Mapping[str, Any]]:
    """Return model metadata loaded from ``path``."""
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8") as fh:
            cfg = json.load(fh)
    except json.JSONDecodeError:  # pragma: no cover - invalid json
        return {}
    models = cfg.get("models")
    if isinstance(models, dict):
        return models
    return {}


def get_model_specs(config_path: Path | None = None) -> Mapping[str, Mapping[str, Any]]:
    """Return model metadata mapping from ``config_path`` or default config."""
    env_path = os.environ.get("LLM_CONFIG_PATH")
    if config_path is None:
        path = Path(env_path) if env_path else _DEFAULT_CONFIG
    else:
        path = config_path
    return _load_model_data(path)


def run_superclaude(prompt: str, model: str) -> str:
    """Return SuperClaude response for ``prompt`` using ``model``."""
    backend = SuperClaudeBackend(model)
    return backend.run(prompt)


register_backend("superclaude", run_superclaude)


def create_default_chain() -> object:
    """Return a simple LangChain chain."""

    try:  # pragma: no cover - optional dependency
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from pydantic import SecretStr
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("langchain is required for the langchain backend") from exc

    if os.environ.get("OPENAI_API_KEY") is None:

        class DummyChain:
            def invoke(self, _data):
                return "ok"

        return DummyChain()

    prompt = ChatPromptTemplate.from_messages([("human", "{input}")])
    api_key = SecretStr(os.environ.get("OPENAI_API_KEY", "sk-dummy"))
    return prompt | ChatOpenAI(api_key=api_key) | StrOutputParser()


def run_langchain(prompt: str) -> str:
    """Return response using a LangChain chain if available."""

    if not os.environ.get("OPENAI_API_KEY"):
        return send_prompt(prompt, model=DEFAULT_MODEL)

    backend = LangChainBackend(create_default_chain())
    return backend.run(prompt)


def _preferred_backends() -> tuple[str, str | None]:
    env_primary = os.environ.get("LLM_PRIMARY_BACKEND")
    env_fallback = os.environ.get("LLM_FALLBACK_BACKEND")
    if env_primary:
        return env_primary, env_fallback
    return get_preferred_models(DEFAULT_PRIMARY_BACKEND, DEFAULT_FALLBACK_BACKEND)


def _run_backend(name: str, prompt: str, model: str) -> str:
    """Return response for ``prompt`` using backend ``name``."""

    func = get_backend(name)
    return func(prompt, model)


def send_prompt(
    prompt: str,
    *,
    local: bool = False,
    model: str = DEFAULT_MODEL,
    strategy: str = "auto",
) -> str:
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

    if strategy in {"cost", "context"} and len(order) > 1:
        specs = get_model_specs()
        primary_model, fallback_model = get_preferred_models(DEFAULT_MODEL, DEFAULT_MODEL)

        def _model_name(backend: str) -> str:
            if backend == primary:
                return primary_model
            if backend == fallback and fallback_model is not None:
                return fallback_model
            return model

        if strategy == "cost":
            order.sort(key=lambda b: specs.get(_model_name(b), {}).get("cost", float("inf")))
        else:  # context
            order.sort(
                key=lambda b: specs.get(_model_name(b), {}).get("context", 0),
                reverse=True,
            )
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
    "run_superclaude",
    "create_default_chain",
    "run_langchain",
    "send_prompt",
]
