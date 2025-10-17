"""Entry point for the ``scripts.tino_cli`` module."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Callable

from . import api


def _print_json(data: Any) -> None:
    print(json.dumps({"status": "ok", "data": data}, default=_json_default))


def _json_default(obj: Any) -> Any:
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


def _run_handler(handler: Callable[..., Any], *args: Any, **kwargs: Any) -> int:
    try:
        result = handler(*args, **kwargs)
    except api.CommandError as exc:  # pragma: no cover - runtime path
        print(json.dumps({"status": "error", "error": str(exc)}), file=sys.stderr)
        return exc.code
    except Exception as exc:  # pragma: no cover - runtime path
        print(json.dumps({"status": "error", "error": str(exc)}), file=sys.stderr)
        return 1
    _print_json(result)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scripts.tino_cli")
    sub = parser.add_subparsers(dest="command", required=True)

    plan_p = sub.add_parser("plan")
    plan_p.add_argument("goal")

    exec_p = sub.add_parser("exec")
    exec_p.add_argument("goal")

    sub.add_parser("list-recipes")

    open_p = sub.add_parser("open-prompt-file")
    open_p.add_argument("path")

    recipe_p = sub.add_parser("run-recipe")
    recipe_p.add_argument("name")
    recipe_p.add_argument("goal")

    record_p = sub.add_parser("record-event")
    record_p.add_argument("name")
    record_p.add_argument("payload")

    toggle_p = sub.add_parser("toggle-plugin")
    toggle_p.add_argument("name")
    toggle_p.add_argument("enable", type=str, choices=["true", "false", "1", "0"])

    sub.add_parser("dashboard")

    for action in [
        "cockpit-up",
        "cockpit-down",
        "cockpit-new-task",
        "cockpit-inject-context",
        "cockpit-research-ingest",
        "cockpit-wishlist-add",
        "cockpit-publish-docs",
    ]:
        action_parser = sub.add_parser(action)
        if action == "cockpit-inject-context":
            action_parser.add_argument("job", nargs="?")
            action_parser.add_argument("message", nargs=argparse.REMAINDER)
        elif action in {"cockpit-new-task", "cockpit-research-ingest", "cockpit-wishlist-add"}:
            action_parser.add_argument("payload")
        action_parser.add_argument("--confirm", action="store_true")

    logs_p = sub.add_parser("cockpit-logs")
    logs_p.add_argument("--limit", type=int, default=200)

    return parser


def _parse_enable(value: str) -> bool:
    return value.lower() in {"true", "1", "yes", "y"}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "plan":
        return _run_handler(api.plan, args.goal)
    if args.command == "exec":
        return _run_handler(api.exec, args.goal)
    if args.command == "list-recipes":
        return _run_handler(api.list_recipes)
    if args.command == "open-prompt-file":
        return _run_handler(api.open_prompt_file, args.path)
    if args.command == "run-recipe":
        return _run_handler(api.run_recipe, args.name, args.goal)
    if args.command == "record-event":
        payload = json.loads(args.payload)
        return _run_handler(api.record_event_cli, args.name, payload)
    if args.command == "toggle-plugin":
        return _run_handler(api.toggle_plugin, args.name, _parse_enable(args.enable))
    if args.command == "dashboard":
        return _run_handler(api.dashboard)
    if args.command == "cockpit-logs":
        return _run_handler(api.cockpit_logs, limit=args.limit)
    if args.command.startswith("cockpit-"):
        payload = getattr(args, "payload", None)
        job_id = None
        if args.command == "cockpit-inject-context":
            job_arg = getattr(args, "job", None)
            message_parts = getattr(args, "message", None) or []
            if message_parts:
                payload = " ".join(message_parts).strip()
            else:
                payload = getattr(args, "payload", None)
            job_id = job_arg
            if job_arg and "::" in job_arg and not payload:
                job_part, message_part = job_arg.split("::", 1)
                job_id = job_part.strip() or None
                payload = message_part.strip()
        return _run_handler(
            api.cockpit_action,
            args.command,
            payload=payload,
            confirm=args.confirm,
            job_id=job_id,
        )

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":  # pragma: no cover - manual execution path
    sys.exit(main())
