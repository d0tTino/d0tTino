#!/usr/bin/env python3
"""Unified CLI for planning, executing and sending prompts."""

from __future__ import annotations

import argparse
import subprocess
import sys
import os
from pathlib import Path
from typing import List, Optional, Any

from llm import router
from llm.backends import initialize
import asyncio
from scripts import ai_exec, recipes, plugins, query_sources, nsm_stats
from scripts.cli_common import (
    read_prompt,
    build_analytics_parser,
)
import requests
from scripts import cli_actions
from telemetry import analytics_default
from ume import events as ume_events
import logging
import time

REPO_ROOT = Path(__file__).resolve().parent.parent

initialize()


def _publish_event(args: argparse.Namespace, name: str, payload: dict[str, Any]) -> None:
    """Record analytics and publish to NATS when configured."""
    cli_actions.record_event_logged(name, payload, enabled=args.analytics)
    if args.analytics and getattr(args, "nats_url", None):
        try:
            asyncio.run(ume_events.publish_event(args.nats_url, name, payload))  # type: ignore[misc,arg-type]

        except Exception as exc:  # noqa: BLE001
            logging.debug("Failed to publish NATS event: %s", exc)


def _cmd_send(args: argparse.Namespace) -> int:
    prompt = read_prompt(args.prompt)
    try:
        output = router.send_prompt(prompt, local=args.local, model=args.model)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(exc, file=sys.stderr)
        _publish_event(args, "ai-cli-send", {"exit_code": 1})
        return 1
    sys.stdout.write(output)
    if not output.endswith("\n"):
        sys.stdout.write("\n")
    _publish_event(args, "ai-cli-send", {"exit_code": 0})
    return 0


def _cmd_plan(args: argparse.Namespace) -> int:
    start = time.time()
    steps = ai_exec.plan(args.goal, config_path=args.config, analytics=args.analytics)
    for step in steps:
        print(step)
    end = time.time()
    _publish_event(
        args,
        "ai-cli-plan",
        {
            "goal": args.goal,
            "step_count": len(steps),
            "start_ts": start,
            "end_ts": end,
            "latency_ms": int((end - start) * 1000),
        },
    )
    return 0


def _cmd_do(args: argparse.Namespace) -> int:
    steps = ai_exec.plan(
        args.goal, config_path=args.config, analytics=args.analytics
    )
    return cli_actions.run_steps(
        "ai-cli-do",
        steps,
        log_path=args.log,
        analytics=args.analytics,
        payload={"goal": args.goal, "step_count": len(steps)},
        nats_url=args.nats_url,
    )


def _cmd_recipe(args: argparse.Namespace) -> int:
    start = time.time()
    mapping = recipes.discover_recipes()
    if args.name not in mapping:
        print(f"Unknown recipe: {args.name}", file=sys.stderr)
        return 1
    recipe_func = mapping[args.name]
    steps = recipe_func(args.goal)
    exit_code = cli_actions.run_recipe(
        args.name,
        args.goal,
        steps,
        log_path=args.log,
        analytics=args.analytics,
        nats_url=args.nats_url,
    )
    end = time.time()
    if exit_code == 0:
        _publish_event(
            args,
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
        )
    return exit_code


def _cmd_plugin(args: argparse.Namespace) -> int:
    return plugins.main(args.plugin_args)


def _cmd_sources(args: argparse.Namespace) -> int:
    matches = query_sources.find_sources(
        name=args.name,
        category=args.category,
        tags=args.tags,
    )
    for item in matches:
        print(f"{item['name']} - {item['url']}")
    return 0 if matches else 1


def _cmd_stats(args: argparse.Namespace) -> int:
    url = os.environ.get("EVENTS_URL")
    if not url:
        print("EVENTS_URL is not set", file=sys.stderr)
        return 1
    try:
        events = list(nsm_stats.iter_events(url))
    except Exception as exc:  # noqa: BLE001
        print(f"failed to fetch events: {exc}", file=sys.stderr)
        return 1
    total = len(events)
    successes = sum(1 for ev in events if ev.get("exit_code") == 0)
    success_rate = successes / total * 100 if total else 0.0
    latencies = []
    for ev in events:
        val = ev.get("latency_ms")
        if isinstance(val, (int, float)):
            latencies.append(float(val))
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    print(f"Total runs: {total}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Average latency: {avg_latency:.2f} ms")
    return 0


def _cmd_metrics(args: argparse.Namespace) -> int:
    """Show weekly totals of successful ai-do runs."""
    url = args.aggregates_url or os.environ.get("NSM_URL")
    if url:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            counts = resp.json()
        except Exception as exc:  # noqa: BLE001
            print(f"failed to fetch aggregates: {exc}", file=sys.stderr)
            return 1
    else:
        source = args.source or os.environ.get("EVENTS_URL")
        if not source:
            print(
                "NSM_URL or --aggregates-url or EVENTS_URL or source required",
                file=sys.stderr,
            )
            return 1
        try:
            events = list(nsm_stats.iter_events(source))
        except Exception as exc:  # noqa: BLE001
            print(f"failed to fetch events: {exc}", file=sys.stderr)
            return 1
        counts = nsm_stats.aggregate_successful_runs(events)
    for dev in sorted(counts):
        for week in sorted(counts[dev]):
            print(f"{dev},{week},{counts[dev][week]}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    analytics = build_analytics_parser()

    analytics.add_argument(
        "--nats-url",
        dest="nats_url",
        default=None,
        help="NATS server URL for telemetry",
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
    do.add_argument(
        "--log",
        type=Path,
        default=REPO_ROOT / "ai_do.log",
        help="Log file path (default: %(default)s)",
    )
    do.set_defaults(func=_cmd_do)

    recipe = sub.add_parser("recipe", help="Execute a named recipe", parents=[analytics])
    recipe.add_argument("name", help="Recipe name")
    recipe.add_argument("goal", help="High level description of the task")
    recipe.add_argument(
        "--log",
        type=Path,
        default=REPO_ROOT / "ai_do.log",
        help="Log file path (default: %(default)s)",
    )
    recipe.set_defaults(func=_cmd_recipe)

    plugin = sub.add_parser("plugin", help="Manage plug-ins")
    plugin.add_argument("plugin_args", nargs=argparse.REMAINDER)
    plugin.set_defaults(func=_cmd_plugin)

    sources = sub.add_parser(
        "sources",
        help="List or search entries in metadata/sources.json",
    )
    sources.add_argument("--name", "-n", help="Filter by name substring")
    sources.add_argument("--category", "-c", help="Filter by category")
    sources.add_argument(
        "--tag",
        "-t",
        action="append",
        dest="tags",
        help="Filter by tag (repeatable)",
    )
    sources.set_defaults(func=_cmd_sources)

    stats = sub.add_parser(
        "stats",
        help="Show aggregated event stats from EVENTS_URL",
    )
    stats.set_defaults(func=_cmd_stats)

    metrics = sub.add_parser(
        "metrics",
        help="Show weekly north star metrics",
    )
    metrics.add_argument(
        "source",
        nargs="?",
        default=None,
        help="EVENTS_URL or path to local file",
    )
    metrics.add_argument(
        "--aggregates-url",
        dest="aggregates_url",
        default=None,
        help="URL for precomputed weekly aggregates (default: NSM_URL)",
    )
    metrics.set_defaults(func=_cmd_metrics)

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


def sources_main(argv: Optional[List[str]] = None) -> int:
    argv = ["sources", *(argv or [])]
    return main(argv)


def metrics_main(argv: Optional[List[str]] = None) -> int:
    argv = ["metrics", *(argv or [])]
    return main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
