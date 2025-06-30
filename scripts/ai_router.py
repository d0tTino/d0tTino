#!/usr/bin/env python3
"""Route prompts to Gemini or Ollama."""


from __future__ import annotations

import argparse
import subprocess
import sys

DEFAULT_MODEL = "llama3"


def run_gemini(prompt: str, model: str | None = None) -> str:
    """Return Gemini response for ``prompt``."""
    cmd = ["gemini"]
    if model:
        cmd += ["--model", model]
    result = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def run_ollama(prompt: str, model: str) -> str:
    """Return Ollama response for ``prompt`` using ``model``."""
    cmd = ["ollama", "run", model, prompt]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def send_prompt(prompt: str, *, local: bool = False, model: str = DEFAULT_MODEL) -> str:
    """Send ``prompt`` to Gemini or Ollama and return the response text."""
    if not local:
        try:
            return run_gemini(prompt, model)
        except (FileNotFoundError, subprocess.CalledProcessError):
            local = True
    if local:
        return run_ollama(prompt, model)
    raise RuntimeError("Unable to process prompt")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", nargs="?", help="Prompt to send to the model")
    parser.add_argument(
        "--local",
        action="store_true",
        help="Use local model via Ollama instead of Gemini",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Model name for Ollama (default: %(default)s)",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read prompt from stdin when no argument is supplied",
    )
    args = parser.parse_args(argv)

    if args.prompt is None:
        if args.stdin:
            args.prompt = sys.stdin.read()
        else:
            parser.error("the following arguments are required: prompt (or --stdin)")

    try:
        output = send_prompt(args.prompt, local=args.local, model=args.model)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(exc, file=sys.stderr)
        return 1

    sys.stdout.write(output)
    if not output.endswith("\n"):
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":

    raise SystemExit(main())
