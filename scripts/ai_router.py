#!/usr/bin/env python3
"""Route prompts to the configured LLM backend."""

from __future__ import annotations

import argparse
import subprocess
import sys

from llm import router
from llm.langchain_backend import LangChainBackend
from typing import Any, cast

DEFAULT_MODEL = router.DEFAULT_MODEL
DEFAULT_COMPLEXITY_THRESHOLD = router.DEFAULT_COMPLEXITY_THRESHOLD

# Backend helpers (overridable in tests)
GeminiDSPyBackend = router.GeminiDSPyBackend
GeminiBackend = router.GeminiBackend
OllamaDSPyBackend = router.OllamaDSPyBackend
OllamaBackend = router.OllamaBackend
OpenRouterDSPyBackend = router.OpenRouterDSPyBackend
OpenRouterBackend = router.OpenRouterBackend


def run_gemini(prompt: str, model: str | None = None) -> str:
    backend_cls = (
        GeminiDSPyBackend if GeminiDSPyBackend is not None else GeminiBackend
    )
    backend = cast(Any, backend_cls)(model)
    return backend.run(prompt)


def run_ollama(prompt: str, model: str) -> str:
    backend_cls = (
        OllamaDSPyBackend if OllamaDSPyBackend is not None else OllamaBackend
    )
    backend = cast(Any, backend_cls)(model)
    return backend.run(prompt)


def run_openrouter(prompt: str, model: str) -> str:
    backend_cls = (
        OpenRouterDSPyBackend if OpenRouterDSPyBackend is not None else OpenRouterBackend
    )
    backend = cast(Any, backend_cls)(model)
    return backend.run(prompt)

def _run_backend(name: str, prompt: str, model: str) -> str:
    if name == "langchain":
        return run_langchain(prompt)
    return router._run_backend(name, prompt, model)


class _EchoChain:
    def invoke(self, data):
        return data.get("input", data)


def run_langchain(prompt: str) -> str:
    """Return response using a basic LangChain chain."""
    backend = LangChainBackend(_EchoChain())
    return backend.run(prompt)


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
            output = router.send_prompt(prompt, local=args.local, model=args.model)

    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(exc, file=sys.stderr)
        return 1

    sys.stdout.write(output)
    if not output.endswith("\n"):
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
