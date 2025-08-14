#!/usr/bin/env python3
"""Unified CLI for planning, executing and sending prompts."""

from __future__ import annotations

import argparse
import subprocess
import sys
import os
import json
from pathlib import Path
from typing import List, Optional, Any
import threading

from llm import router
from llm.backends import initialize
import asyncio
from scripts import ai_exec, recipes, plugins, query_sources, nsm_stats, ai_suggest
from scripts.cli_common import (
    PlanStep,
    read_prompt,
    build_analytics_parser,
)
import requests
from scripts import cli_actions
from telemetry import analytics_default
from ume import events as ume_events
import logging
import time
import importlib

SESSION_FILE = Path.home() / ".config" / "d0tTino" / "cli_session.json"
_session: dict[str, Any] = {}


def _load_session() -> None:
    global _session
    try:
        _session = json.loads(SESSION_FILE.read_text())
    except Exception:
        _session = {}


_load_session()

REPO_ROOT = Path(__file__).resolve().parent.parent

initialize()


def _cmd_login(args: argparse.Namespace) -> int:
    data = {"user_id": args.user_id}
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(json.dumps(data))
    _session.update(data)
    _publish_event(args, "ai-cli-login", {**data, "exit_code": 0})
    return 0


def _cmd_switch_context(args: argparse.Namespace) -> int:
    data = {**_session, "context": args.context}
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(json.dumps(data))
    _session.update(data)
    _publish_event(args, "ai-cli-switch-context", {"context": args.context, "exit_code": 0})
    return 0


def _publish_event(args: argparse.Namespace, name: str, payload: dict[str, Any]) -> None:
    """Record analytics and publish to NATS when configured."""
    if "user_id" not in payload and _session.get("user_id"):
        payload = {"user_id": _session["user_id"], **payload}
    if "context" not in payload and _session.get("context"):
        payload = {"context": _session["context"], **payload}
    cli_actions.record_event_logged(name, payload, enabled=args.analytics)
    if args.analytics and getattr(args, "nats_url", None):
        try:
            asyncio.run(ume_events.publish_event(args.nats_url, name, payload))

        except Exception as exc:  # noqa: BLE001
            logging.debug("Failed to publish NATS event: %s", exc)


def _cmd_send(args: argparse.Namespace) -> int:
    prompt = read_prompt(args.prompt)
    try:
        kwargs = {"local": args.local, "model": args.model}
        if _session.get("context"):
            kwargs["context"] = _session["context"]
        output = router.send_prompt(prompt, **kwargs)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(exc, file=sys.stderr)
        _publish_event(args, "ai-cli-send", {"exit_code": 1})
        return 1
    sys.stdout.write(output)
    if not output.endswith("\n"):
        sys.stdout.write("\n")
    _publish_event(args, "ai-cli-send", {"exit_code": 0})
    return 0


def _cmd_suggest(args: argparse.Namespace) -> int:
    try:
        kwargs = {"local": args.local, "model": args.model}
        if _session.get("context"):
            kwargs["context"] = _session["context"]
        suggestions = ai_suggest.suggest(args.goal, **kwargs)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(exc, file=sys.stderr)
        _publish_event(args, "ai-cli-suggest", {"exit_code": 1})
        return 1
    for line in suggestions:
        print(line)
    _publish_event(
        args,
        "ai-cli-suggest",
        {"exit_code": 0, "suggestion_count": len(suggestions)},
    )
    return 0


def _clarify_goal(
    goal: str, *, config, analytics: bool
) -> tuple[str, List[PlanStep]]:
    """Request clarification from the user until planning succeeds.

    ``ai_exec.plan`` may return an empty list when the goal is ambiguous or
    lacks sufficient detail. In that case ask the user for more context and
    re-run planning with the expanded goal.
    """
    steps = ai_exec.plan(goal, config_path=config, analytics=analytics)
    while not steps:
        extra = input("Goal unclear. Please provide more details: ").strip()
        if not extra:
            break
        goal = f"{goal}. {extra}" if goal else extra
        steps = ai_exec.plan(goal, config_path=config, analytics=analytics)
    return goal, steps


def _cmd_plan(args: argparse.Namespace) -> int:
    start = time.time()
    goal, steps = _clarify_goal(
        args.goal, config=args.config, analytics=args.analytics
    )
    for step in steps:
        print(f"{step.number}. {step.command}")
        if step.diff:
            print(step.diff)

    end = time.time()
    _publish_event(
        args,
        "ai-cli-plan",
        {
            "goal": goal,
            "step_count": len(steps),
            "start_ts": start,
            "end_ts": end,
            "latency_ms": int((end - start) * 1000),
        },
    )
    return 0


def _cmd_do(args: argparse.Namespace) -> int:
    goal, steps = _clarify_goal(
        args.goal, config=args.config, analytics=args.analytics
    )
    kwargs: dict[str, Any] = {
        "log_path": args.log,
        "analytics": args.analytics,
        "payload": {"goal": goal, "step_count": len(steps)},
        "nats_url": args.nats_url,
        "jetstream": getattr(args, "jetstream", False),
    }
    if getattr(args, "dry_run", False):
        kwargs["dry_run"] = True
    if getattr(args, "yes", False):
        kwargs["assume_yes"] = True
    if getattr(args, "confirm", False):
        kwargs["confirm"] = True
    return cli_actions.run_steps("ai-cli-do", steps, **kwargs)


def _cmd_recipe(args: argparse.Namespace) -> int:
    start = time.time()
    mapping = recipes.discover_recipes()
    if args.name not in mapping:
        print(f"Unknown recipe: {args.name}", file=sys.stderr)
        return 1
    recipe_func = mapping[args.name]
    steps = recipe_func(args.goal)
    kwargs: dict[str, Any] = {
        "log_path": args.log,
        "analytics": args.analytics,
        "nats_url": args.nats_url,
        "jetstream": getattr(args, "jetstream", False),
    }
    if getattr(args, "dry_run", False):
        kwargs["dry_run"] = True
    if getattr(args, "yes", False):
        kwargs["assume_yes"] = True
    if getattr(args, "confirm", False):
        kwargs["confirm"] = True
    exit_code = cli_actions.run_recipe(args.name, args.goal, steps, **kwargs)
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


def _cmd_status(args: argparse.Namespace) -> int:
    """Show remaining budget and routing mode."""
    budget = router.get_budget()
    mode = os.environ.get("LLM_ROUTING_MODE", "auto")
    print(f"Budget remaining: {budget}")
    print(f"Routing mode: {mode}")
    return 0


def _cmd_finance_analyze(args: argparse.Namespace) -> int:
    payload: dict[str, Any] = {
        "workflow": "FinancialDecisionSupport",
        "parameters": {"max_options": args.max_options},
    }
    params = payload["parameters"]
    if args.min_budget is not None:
        params["min_budget"] = args.min_budget
    if args.max_budget is not None:
        params["max_budget"] = args.max_budget
    if getattr(args, "monthly_budget", None) is not None:
        params["monthly_budget"] = args.monthly_budget
    stop = threading.Event()
    listener: threading.Thread | None = None

    if not getattr(args, "no_progress", False):
        
        def _listen() -> None:
            async def _run() -> None:
                try:
                    async for ev in ume_events.iter_events(url=args.nats_url):
                        if stop.is_set():
                            break
                        if ev.get("name") == "finance-analyze-progress":
                            cnt = ev.get("options_generated")
                            if isinstance(cnt, int):
                                print(
                                    f"{cnt} options generated. View them with `ai finance view`."
                                )
                except Exception:  # pragma: no cover - best effort logging
                    logging.debug("progress listener stopped")
            asyncio.run(_run())

        listener = threading.Thread(target=_listen, daemon=True)
        listener.start()

    try:
        text = router.send_prompt(json.dumps(payload))
        data = json.loads(text)
        options = data.get("options", [])
    except Exception as exc:  # noqa: BLE001
        print(exc, file=sys.stderr)
        _publish_event(args, "finance-analyze", {"exit_code": 1})
        stop.set()
        if listener:
            listener.join()
        return 1
    finally:
        stop.set()
        if listener:
            listener.join()

    for idx, _ in enumerate(options, start=1):
        _publish_event(
            args,
            "finance-analyze-progress",
            {"options_generated": idx},
        )
    _publish_event(
        args,
        "finance-analyze",
        {"exit_code": 0, "option_count": len(options)},
    )
    return 0


def _cmd_finance_view(args: argparse.Namespace) -> int:
    base = args.url or os.environ.get("FINANCE_URL")
    if not base:
        print("Finance URL required (--url or FINANCE_URL)", file=sys.stderr)

        return 1
    try:
        resp = requests.get(f"{base}/v1/finance/options", timeout=10)
        resp.raise_for_status()
        options = resp.json()
    except Exception as exc:  # noqa: BLE001
        print(f"failed to fetch options: {exc}", file=sys.stderr)
        return 1
    if args.timeline:
        for opt in options:
            name = opt.get("name", "")
            for ev in opt.get("timeline", []):
                when = ev.get("time") or ev.get("date") or ""
                desc = ev.get("detail") or ev.get("description") or ""
                print(f"{when} {name} {desc}".strip())
    else:
        print(f"{'Name':<20} {'Cost':<10} {'Summary'}")
        for opt in options:
            print(
                f"{opt.get('name',''):<20} {str(opt.get('cost','')):<10} {opt.get('summary','')}",
            )

    return 0


def _cmd_metrics(args: argparse.Namespace) -> int:
    """Show weekly totals of successful ai-do runs."""
    if args.aggregates_url:
        url = args.aggregates_url or os.environ.get("NSM_URL")
        if not url:
            print("NSM_URL or --aggregates-url required", file=sys.stderr)
            return 1
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
            print("EVENTS_URL or source required", file=sys.stderr)
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


def _load_calendar_agent() -> type[Any] | None:
    """Load and return the calendar NLP agent class if available."""
    try:
        module = importlib.import_module("calendar_nlp")
        return getattr(module, "CalendarNLP_Agent")
    except (ImportError, AttributeError):
        return None


def _cmd_calendar_add(args: argparse.Namespace) -> int:
    start = time.time()
    agent_cls = _load_calendar_agent()
    if agent_cls is None:
        msg = (
            "CalendarNLP_Agent is not available. Install or enable the calendar plugin."
        )
        print(msg, file=sys.stderr)
        end = time.time()
        cli_actions.record_event_logged(
            "ai-cli-calendar-add",
            {
                "exit_code": 1,
                "start_ts": start,
                "end_ts": end,
                "latency_ms": int((end - start) * 1000),
                "error": msg,
            },
            enabled=args.analytics,
        )
        return 1
    try:
        agent = agent_cls()
        agent.add_event(args.text)
    except Exception as exc:  # noqa: BLE001
        end = time.time()
        print(exc, file=sys.stderr)
        cli_actions.record_event_logged(
            "ai-cli-calendar-add",
            {
                "exit_code": 1,
                "start_ts": start,
                "end_ts": end,
                "latency_ms": int((end - start) * 1000),
            },
            enabled=args.analytics,
        )
        return 1
    end = time.time()
    cli_actions.record_event_logged(
        "ai-cli-calendar-add",
        {
            "exit_code": 0,
            "start_ts": start,
            "end_ts": end,
            "latency_ms": int((end - start) * 1000),
        },
        enabled=args.analytics,
    )
    return 0


def _cmd_calendar_view(args: argparse.Namespace) -> int:
    base = args.url or os.environ.get("CALENDAR_URL")
    if not base:
        print("Calendar URL required (--url or CALENDAR_URL)", file=sys.stderr)
        return 1
    params: dict[str, Any] = {}
    if args.day:
        params["day"] = args.day
    if args.week:
        params["week"] = args.week
    if args.layers:
        params["layers"] = ",".join(args.layers)
    try:
        resp = requests.get(f"{base}/v1/calendar/events", params=params, timeout=10)
        resp.raise_for_status()
        events = resp.json()
    except Exception as exc:  # noqa: BLE001
        print(f"failed to fetch events: {exc}", file=sys.stderr)
        return 1
    if args.timeline:
        for ev in events:
            start = ev.get("start", "")
            end = ev.get("end", "")
            summary = ev.get("summary", "")
            if end:
                print(f"{start} - {end} {summary}".strip())
            else:
                print(f"{start} {summary}".strip())
    else:
        print(f"{'Start':<20} {'End':<20} {'Summary':<30} {'Layer':<10}")
        for ev in events:
            layer = ev.get("layer")
            if layer is None:
                layer = ",".join(str(x) for x in ev.get("layers", []))
            print(
                f"{ev.get('start',''):<20} {ev.get('end',''):<20} {ev.get('summary',''):<30} {layer}"
            )
    return 0


def build_parser() -> argparse.ArgumentParser:
    analytics = build_analytics_parser()

    analytics.add_argument(
        "--enable-mcp",
        action="store_true",
        dest="enable_mcp",
        help="Load MCP plug-ins exposing additional tools",
    )

    analytics.add_argument(
        "--nats-url",
        dest="nats_url",
        default=None,
        help="NATS server URL for telemetry",
    )
    parser = argparse.ArgumentParser(description=__doc__, parents=[analytics])
    sub = parser.add_subparsers(dest="command", required=True)
    login = sub.add_parser("login", help="Authenticate user", parents=[analytics])
    login.add_argument("user_id", help="Identifier to persist for the session")
    login.set_defaults(func=_cmd_login)
    switch_context = sub.add_parser(
        "switch-context", help="Switch active context", parents=[analytics]
    )
    switch_context.add_argument(
        "context",
        choices=("personal", "group"),
        help="Context identifier (personal or group)",
    )
    switch_context.set_defaults(func=_cmd_switch_context)
    send = sub.add_parser("send", help="Send a prompt to the LLM backend", parents=[analytics])
    send.add_argument("prompt", help="Prompt or '-' to read from STDIN")
    send.add_argument("--local", action="store_true", help="Force use of fallback backend")
    send.add_argument("--model", default=router.DEFAULT_MODEL, help="Model name for Ollama (default: %(default)s)")
    send.set_defaults(func=_cmd_send)

    plan = sub.add_parser("plan", help="Generate a shell plan for a goal", parents=[analytics])
    plan.add_argument("goal")
    plan.add_argument("--config")
    plan.set_defaults(func=_cmd_plan)

    suggest = sub.add_parser(
        "suggest", help="Suggest shell commands for a goal", parents=[analytics]
    )
    suggest.add_argument("goal")
    suggest.add_argument(
        "--local", action="store_true", help="Force use of fallback backend"
    )
    suggest.add_argument(
        "--model",
        default=router.DEFAULT_MODEL,
        help="Model name for Ollama (default: %(default)s)",
    )
    suggest.set_defaults(func=_cmd_suggest)

    do = sub.add_parser("do", help="Interactively execute a goal", parents=[analytics])
    do.add_argument("goal")
    do.add_argument("--config")
    do.add_argument(
        "--log",
        type=Path,
        default=REPO_ROOT / "ai_do.log",
        help="Log file path (default: %(default)s)",
    )
    do.add_argument(
        "--jetstream",
        action="store_true",
        help="Publish events via JetStream",
    )
    do.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing",
    )
    do.add_argument(
        "--yes",
        action="store_true",
        help="Run without interactive prompts for non-risky commands",
    )
    do.add_argument(
        "--confirm",
        action="store_true",
        help="Also run commands tagged [risk:*] without prompting",
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
    recipe.add_argument(
        "--jetstream",
        action="store_true",
        help="Publish events via JetStream",
    )
    recipe.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing",
    )
    recipe.add_argument(
        "--yes",
        action="store_true",
        help="Run without interactive prompts for non-risky commands",
    )
    recipe.add_argument(
        "--confirm",
        action="store_true",
        help="Also run commands tagged [risk:*] without prompting",
    )
    recipe.set_defaults(func=_cmd_recipe)

    plugin = sub.add_parser("plugin", help="Manage plug-ins")
    plugin.add_argument("plugin_args", nargs=argparse.REMAINDER)
    plugin.set_defaults(func=_cmd_plugin)

    finance = sub.add_parser(
        "finance", help="Financial decision support", parents=[analytics]
    )
    finance_sub = finance.add_subparsers(dest="finance_command", required=True)
    analyze = finance_sub.add_parser(
        "analyze", help="Analyze financial options", parents=[analytics]
    )
    analyze.add_argument(
        "--max-options",
        type=int,
        default=3,
        dest="max_options",
        help="Maximum number of options to generate (default: %(default)s)",
    )
    analyze.add_argument(
        "--min-budget", type=float, dest="min_budget", default=None
    )
    analyze.add_argument(
        "--max-budget", type=float, dest="max_budget", default=None
    )
    analyze.add_argument(
        "--monthly-budget", type=float, dest="monthly_budget", default=None
    )
    analyze.add_argument(
        "--no-progress",
        action="store_true",
        dest="no_progress",
        help="Disable live progress updates",
    )
    analyze.set_defaults(func=_cmd_finance_analyze)

    view = finance_sub.add_parser(
        "view", help="View financial options", parents=[analytics]
    )
    view.add_argument(
        "--url",
        dest="url",
        default=None,
        help="Base URL for finance service",

    )
    view.add_argument(
        "--timeline",
        action="store_true",
        dest="timeline",
        help="Display options as timeline",
    )

    view.set_defaults(func=_cmd_finance_view)

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

    status = sub.add_parser(
        "status",
        help="Show remaining budget and routing mode",
        parents=[analytics],
    )
    status.set_defaults(func=_cmd_status)

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

    calendar = sub.add_parser("calendar", help="Manage calendar events", parents=[analytics])
    cal_sub = calendar.add_subparsers(dest="calendar_cmd", required=True)

    cal_add = cal_sub.add_parser("add", help="Add calendar event", parents=[analytics])
    cal_add.add_argument("text", help="Event description")
    cal_add.set_defaults(func=_cmd_calendar_add)

    cal_view = cal_sub.add_parser("view", help="View calendar events", parents=[analytics])
    group = cal_view.add_mutually_exclusive_group(required=True)
    group.add_argument("--day", dest="day")
    group.add_argument("--week", dest="week")
    cal_view.add_argument(
        "--layers",
        nargs="+",
        dest="layers",
        default=None,
        help="Filter by layers",
    )
    cal_view.add_argument(
        "--timeline",
        action="store_true",
        help="Display events as timeline",
    )
    cal_view.add_argument(
        "--url",
        dest="url",
        default=None,
        help="Calendar service base URL (default: CALENDAR_URL)",
    )
    cal_view.set_defaults(func=_cmd_calendar_view)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.analytics = getattr(args, "analytics", analytics_default())
    if getattr(args, "enable_mcp", False):
        try:
            mcp = importlib.import_module("plugins.mcp")
            mcp.get_tools()
        except Exception as exc:  # noqa: BLE001
            logging.debug("Failed to load MCP plug-ins: %s", exc)
    return args.func(args)


def login_main(argv: Optional[List[str]] = None) -> int:
    argv = ["login", *(argv or [])]
    return main(argv)


def switch_context_main(argv: Optional[List[str]] = None) -> int:
    argv = ["switch-context", *(argv or [])]
    return main(argv)


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
