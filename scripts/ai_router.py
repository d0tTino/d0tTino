#!/usr/bin/env python3
"""Route prompts to the configured LLM backend."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

from llm.backends import (
    GeminiBackend,
    OllamaBackend,
    OpenRouterBackend,
    GeminiDSPyBackend,
    OllamaDSPyBackend,
    OpenRouterDSPyBackend,
    LangChainBackend,
)
from llm.ai_router import get_preferred_models

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


def create_default_chain() -> object:
    """Return a simple LangChain chain."""
    try:  # pragma: no cover - optional dependency
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("langchain is required for the langchain backend") from exc

    prompt = ChatPromptTemplate.from_messages([("human", "{input}")])
    return prompt | ChatOpenAI() | StrOutputParser()


def run_langchain(prompt: str) -> str:
    """Return response using a LangChain chain."""
    backend = LangChainBackend(create_default_chain())
    return backend.run(prompt)


def _preferred_backends() -> tuple[str, str | None]:
    env_primary = os.environ.get("LLM_PRIMARY_BACKEND")
    env_fallback = os.environ.get("LLM_FALLBACK_BACKEND")
    if env_primary:
        return env_primary, env_fallback
    return get_preferred_models(
        DEFAULT_PRIMARY_BACKEND, DEFAULT_FALLBACK_BACKEND
    )


def _run_backend(name: str, prompt: str, model: str) -> str:
    name = name.lower()
    if name == "gemini":
        return run_gemini(prompt, model)
    if name == "ollama":
        return run_ollama(prompt, model)
    if name == "openrouter":
        return run_openrouter(prompt, model)
    if name == "langchain":
        return run_langchain(prompt)
    raise ValueError(f"Unknown backend: {name}")


def send_prompt(prompt: str, *, local: bool = False, model: str = DEFAULT_MODEL) -> str:
    """Send ``prompt`` using the configured backends."""
    primary, fallback = _preferred_backends()
    order: list[str] = []

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
            threshold = int(
                os.environ.get("LLM_COMPLEXITY_THRESHOLD", DEFAULT_COMPLEXITY_THRESHOLD)
            )
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "prompt",
        help="Prompt to send to the model or '-' to read from STDIN",
    )

    parser.add_argument(
        "--local",
        action="store_true",
        help="Force use of the fallback backend",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Model name for Ollama (default: %(default)s)",
    )
    parser.add_argument(
        "--backend",
        choices=["gemini", "ollama", "openrouter", "langchain"],
        help="Explicit backend to use",
    )
    args = parser.parse_args(argv)

    prompt = args.prompt
    if prompt == "-":
        prompt = sys.stdin.read()


    try:
        if args.backend:
            output = _run_backend(args.backend, prompt, args.model)
        else:
            output = send_prompt(prompt, local=args.local, model=args.model)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(exc, file=sys.stderr)
        return 1

    sys.stdout.write(output)
    if not output.endswith("\n"):
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
