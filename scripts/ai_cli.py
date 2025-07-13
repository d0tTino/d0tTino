#!/usr/bin/env python3
"""Unified CLI for planning, executing and sending prompts."""

from __future__ import annotations

import argparse
import subprocess
import sys
import logging
from pathlib import Path
from typing import List, Optional

from llm import router
from llm.backends import load_backends
from scripts import ai_exec, ai_do, recipes, plugins
from scripts.cli_common import execute_steps, read_prompt
from telemetry import record_event, analytics_default
import time

load_backends()


def _cmd_send(args: argparse.Namespace) -> int:
    prompt = read_prompt(args.prompt)
    try:
        output = router.send_prompt(prompt, local=args.local, model=args.model)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(exc, file=sys.stderr)
        success = record_event("ai-cli-send", {"exit_code": 1}, enabled=args.analytics)
        if not success:
            logging.debug("Failed to record telemetry")
        return 1
    sys.stdout.write(output)
    if not output.endswith("\n"):
        sys.stdout.write("\n")
    success = record_event("ai-cli-send", {"exit_code": 0}, enabled=args.analytics)
    if not success:
        logging.debug("Failed to record telemetry")
    return 0


def _cmd_plan(args: argparse.Namespace) -> int:
    start = time.time()
    steps = ai_exec.plan(args.goal, config_path=args.config, analytics=args.analytics)
    for step in steps:
        print(step)
    end = time.time()
    success = record_event(
        "ai-cli-plan",
        {
            "goal": args.goal,
            "step_count": len(steps),
            "start_ts": start,
            "end_ts": end,
            "latency_ms": int((end - start) * 1000),
        },
        enabled=args.analytics,
    )
    if not success:
        logging.debug("Failed to record telemetry")
    return 0


def _cmd_do(args: argparse.Namespace) -> int:
    start = time.time()
    steps = ai_exec.plan(
        args.goal, config_path=args.config, analytics=args.analytics
    )
    exit_code = execute_steps(steps, log_path=args.log)
    end = time.time()
    success = record_event(
        "ai-cli-do",
        {
            "goal": args.goal,
            "exit_code": exit_code,
            "start_ts": start,
            "end_ts": end,
            "latency_ms": int((end - start) * 1000),
        },
        enabled=args.analytics,
    )
    if not success:
        logging.debug("Failed to record telemetry")
    return exit_code


def _cmd_recipe(args: argparse.Namespace) -> int:
    start = time.time()
    mapping = recipes.discover_recipes()
    if args.name not in mapping:
        print(f"Unknown recipe: {args.name}", file=sys.stderr)
        return 1
    recipe_func = mapping[args.name]
    steps = recipe_func(args.goal)
    exit_code = ai_do.run_recipe(
        args.name,
        args.goal,
        steps,
        log_path=args.log,
        analytics=args.analytics,
    )
    end = time.time()
    if exit_code == 0:
        success = record_event(
            "ai-cli-recipe",
            {
                "recipe": args.name,
                "goal": args.goal,
                "exit_code": exit_code,
                "step_count": len(steps),
                "start_ts": start,
                "end_ts": end,
                "latency_ms": int((end - start) * 1000),
            },
            enabled=args.analytics,
        )
        if not success:
            logging.debug("Failed to record telemetry")
    return exit_code


def _cmd_plugin(args: argparse.Namespace) -> int:
    return plugins.main(args.plugin_args)


def build_parser() -> argparse.ArgumentParser:
    analytics = argparse.ArgumentParser(add_help=False)
    analytics.add_argument(
        "--analytics",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Record anonymous usage events",
    )

    parser = argparse.ArgumentParser(description=__doc__, parents=[analytics])
    sub = parser.add_subparsers(dest="command", required=True)
    send = sub.add_parser("send", help="Send a prompt to the LLM backend", parents=[analytics])
    send.add_argument("prompt", help="Prompt or '-' to read from STDIN")
    send.add_argument("--local", action="store_true", help="Force use of fallback backend")
    send.add_argument("--model", default=router.DEFAULT_MODEL, help="Model name for Ollama (default: %(default)s)")
    send.set_defaults(func=_cmd_send)

    plan = sub.add_parser("plan", help="Generate a shell plan for a goal", parents=[analytics])
    plan.add_argument("goal")
    plan.add_argument("--config")
    plan.set_defaults(func=_cmd_plan)

    do = sub.add_parser("do", help="Interactively execute a goal", parents=[analytics])
    do.add_argument("goal")
    do.add_argument("--config")
    do.add_argument("--log", type=Path, default=Path("ai_do.log"), help="Log file path (default: %(default)s)")
    do.set_defaults(func=_cmd_do)

    recipe = sub.add_parser("recipe", help="Execute a named recipe", parents=[analytics])
    recipe.add_argument("name", help="Recipe name")
    recipe.add_argument("goal", help="High level description of the task")
    recipe.add_argument("--log", type=Path, default=Path("ai_do.log"), help="Log file path (default: %(default)s)")
    recipe.set_defaults(func=_cmd_recipe)

    plugin = sub.add_parser("plugin", help="Manage plug-ins")
    plugin.add_argument("plugin_args", nargs=argparse.REMAINDER)
    plugin.set_defaults(func=_cmd_plugin)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.analytics = getattr(args, "analytics", analytics_default())
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


def recipe_main(argv: Optional[List[str]] = None) -> int:
    argv = ["recipe", *(argv or [])]
    return main(argv)


def plugin_main(argv: Optional[List[str]] = None) -> int:
    argv = ["plugin", *(argv or [])]
    return main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
