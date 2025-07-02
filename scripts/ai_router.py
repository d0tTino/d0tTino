#!/usr/bin/env python3
"""Route prompts to the configured LLM backend."""

from __future__ import annotations

import argparse
import subprocess
import sys
import os

from llm import router
from llm.backends import (
    GeminiBackend,
    OllamaBackend,
    OpenRouterBackend,
    GeminiDSPyBackend,
    OllamaDSPyBackend,
    OpenRouterDSPyBackend,
    LangChainBackend,
)

DEFAULT_MODEL = router.DEFAULT_MODEL
DEFAULT_PRIMARY_BACKEND = router.DEFAULT_PRIMARY_BACKEND
DEFAULT_FALLBACK_BACKEND = router.DEFAULT_FALLBACK_BACKEND
DEFAULT_COMPLEXITY_THRESHOLD = router.DEFAULT_COMPLEXITY_THRESHOLD


run_gemini = router.run_gemini
run_ollama = router.run_ollama

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
    """Return response using a LangChain chain if available."""
    if not os.environ.get("OPENAI_API_KEY"):
        # Fallback to the standard routing logic when no API key is set.
        return router.send_prompt(prompt, model=DEFAULT_MODEL)

    backend = LangChainBackend(create_default_chain())
    return backend.run(prompt)

def _run_backend(name: str, prompt: str, model: str) -> str:
    """Delegate to ``router._run_backend`` with LangChain support."""
    if name.lower() == "langchain":
        return run_langchain(prompt)
    return router._run_backend(name, prompt, model)

def send_prompt(prompt: str, *, local: bool = False, model: str = DEFAULT_MODEL) -> str:
    """Proxy to ``router.send_prompt`` so tests can monkeypatch it."""
    return router.send_prompt(prompt, local=local, model=model)



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

__all__ = [
    "DEFAULT_MODEL",
    "DEFAULT_PRIMARY_BACKEND",
    "DEFAULT_FALLBACK_BACKEND",
    "DEFAULT_COMPLEXITY_THRESHOLD",
    "run_gemini",
    "run_ollama",
    "run_openrouter",
    "run_langchain",
    "create_default_chain",
    "_run_backend",
    "send_prompt",
    "main",
    "GeminiBackend",
    "OllamaBackend",
    "OpenRouterBackend",
    "GeminiDSPyBackend",
    "OllamaDSPyBackend",
    "OpenRouterDSPyBackend",
]
