#!/usr/bin/env python3
"""Route prompts to the configured LLM backend."""

from __future__ import annotations

import argparse
import subprocess
import sys

from llm import router

DEFAULT_MODEL = router.DEFAULT_MODEL


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
    args = parser.parse_args(argv)

    prompt = args.prompt
    if prompt == "-":
        prompt = sys.stdin.read()

    try:
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
