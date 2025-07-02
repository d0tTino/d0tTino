#!/usr/bin/env python3
"""Unified CLI for planning, executing and sending prompts."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from llm import router
from scripts import ai_exec
from scripts.cli_common import execute_steps, read_prompt


def _cmd_send(args: argparse.Namespace) -> int:
    prompt = read_prompt(args.prompt)
    try:
        output = router.send_prompt(prompt, local=args.local, model=args.model)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(exc, file=sys.stderr)
        return 1
    sys.stdout.write(output)
    if not output.endswith("\n"):
        sys.stdout.write("\n")
    return 0


def _cmd_plan(args: argparse.Namespace) -> int:
    steps = ai_exec.plan(args.goal, config_path=args.config)
    for step in steps:
        print(step)
    return 0


def _cmd_do(args: argparse.Namespace) -> int:
    steps = ai_exec.plan(args.goal, config_path=args.config)
    return execute_steps(steps, log_path=args.log)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    send = sub.add_parser("send", help="Send a prompt to the LLM backend")
    send.add_argument("prompt", help="Prompt or '-' to read from STDIN")
    send.add_argument("--local", action="store_true", help="Force use of fallback backend")
    send.add_argument("--model", default=router.DEFAULT_MODEL, help="Model name for Ollama (default: %(default)s)")
    send.set_defaults(func=_cmd_send)

    plan = sub.add_parser("plan", help="Generate a shell plan for a goal")
    plan.add_argument("goal")
    plan.add_argument("--config")
    plan.set_defaults(func=_cmd_plan)

    do = sub.add_parser("do", help="Interactively execute a goal")
    do.add_argument("goal")
    do.add_argument("--config")
    do.add_argument("--log", type=Path, default=Path("ai_do.log"), help="Log file path (default: %(default)s)")
    do.set_defaults(func=_cmd_do)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def plan_main(argv: Optional[List[str]] = None) -> int:
    argv = ["plan", *(argv or [])]
    return main(argv)


def do_main(argv: Optional[List[str]] = None) -> int:
    argv = ["do", *(argv or [])]
    return main(argv)


def send_main(argv: Optional[List[str]] = None) -> int:
    argv = ["send", *(argv or [])]
    return main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
