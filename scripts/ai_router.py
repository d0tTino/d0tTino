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
    GeminiDSPyBackend,
    OllamaBackend,
    OllamaDSPyBackend,

    OpenRouterBackend,
    OpenRouterDSPyBackend,
)

DEFAULT_MODEL = router.DEFAULT_MODEL
DEFAULT_COMPLEXITY_THRESHOLD = router.DEFAULT_COMPLEXITY_THRESHOLD


def run_gemini(prompt: str, model: str | None = None) -> str:
    backend_cls = GeminiDSPyBackend if GeminiDSPyBackend is not None else GeminiBackend
    backend = backend_cls(model)  # type: ignore[arg-type]
    
    return backend.run(prompt)


def run_ollama(prompt: str, model: str) -> str:
    backend_cls = OllamaDSPyBackend if OllamaDSPyBackend is not None else OllamaBackend
    backend = backend_cls(model)  # type: ignore[arg-type]

    return backend.run(prompt)


def run_openrouter(prompt: str, model: str) -> str:
    backend_cls = (
        OpenRouterDSPyBackend if OpenRouterDSPyBackend is not None else OpenRouterBackend
    )
    backend = backend_cls(model)  # type: ignore[arg-type]
    return backend.run(prompt)


def run_langchain(prompt: str) -> str:  # pragma: no cover - placeholder
    return f"langchain:{prompt}"



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
    primary, fallback = router._preferred_backends()
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
            try:
                threshold = int(
                    os.environ.get("LLM_COMPLEXITY_THRESHOLD", DEFAULT_COMPLEXITY_THRESHOLD)
                )
            except ValueError:
                threshold = DEFAULT_COMPLEXITY_THRESHOLD
            complexity = router.estimate_prompt_complexity(prompt)
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
