#!/usr/bin/env python3
"""Route prompts to Gemini CLI or Ollama models."""

from __future__ import annotations

import argparse
import subprocess
from typing import Sequence


def run_gemini(prompt: str) -> subprocess.CompletedProcess:
    """Invoke the Gemini CLI with ``prompt``."""
    return subprocess.run(["gemini", prompt], check=True)


def run_ollama(prompt: str, model: str) -> subprocess.CompletedProcess:
    """Invoke Ollama to run ``model`` with ``prompt``."""
    return subprocess.run(["ollama", "run", model, prompt], check=True)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the :mod:`ai_router` script."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt")
    parser.add_argument(
        "--backend",
        choices=["gemini", "ollama", "auto"],
        default="auto",
        help="Which backend to use (default: auto)",
    )
    parser.add_argument(
        "--model",
        default="llama3",
        help="Model to use with Ollama when applicable",
    )
    args = parser.parse_args(argv)

    try:
        if args.backend == "gemini":
            run_gemini(args.prompt)
        elif args.backend == "ollama":
            run_ollama(args.prompt, args.model)
        else:  # auto
            try:
                run_gemini(args.prompt)
            except (subprocess.CalledProcessError, FileNotFoundError):
                run_ollama(args.prompt, args.model)
    except subprocess.CalledProcessError as exc:
        return exc.returncode
    except FileNotFoundError:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
