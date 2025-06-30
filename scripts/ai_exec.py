#!/usr/bin/env python3
"""Plan and execute shell commands using the configured LLM backend."""

from __future__ import annotations

import argparse
import subprocess
from typing import Iterable

from scripts import ai_router


PLAN_TEMPLATE = """\
Plan the shell commands needed to accomplish this task:
{instruction}
Return one command per line with no explanations.
"""


def plan_commands(instruction: str, *, local: bool = False, model: str = ai_router.DEFAULT_MODEL) -> list[str]:
    """Return a list of shell commands for ``instruction``."""
    prompt = PLAN_TEMPLATE.format(instruction=instruction)
    output = ai_router.send_prompt(prompt, local=local, model=model)
    return [line.strip() for line in output.splitlines() if line.strip()]


def confirm(cmd: str) -> bool:
    """Return ``True`` if the user confirms running ``cmd``."""
    resp = input(f"Run '{cmd}'? [y/N]: ")
    return resp.strip().lower().startswith("y")


def run_commands(commands: Iterable[str]) -> int:
    """Run each command after confirmation. Return the last return code."""
    rc = 0
    for cmd in commands:
        print(cmd)
        if confirm(cmd):
            completed = subprocess.run(cmd, shell=True)
            rc = completed.returncode
            if rc != 0:
                break
    return rc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("instruction", help="Task description for the planner")
    parser.add_argument(
        "--local",
        action="store_true",
        help="Use local model via Ollama instead of Gemini",
    )
    parser.add_argument(
        "--model",
        default=ai_router.DEFAULT_MODEL,
        help="Model name for planning (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    commands = plan_commands(args.instruction, local=args.local, model=args.model)
    return run_commands(commands)


if __name__ == "__main__":
    raise SystemExit(main())
