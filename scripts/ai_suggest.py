#!/usr/bin/env python3
"""Suggest up to three shell commands for a goal with risk labels."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from typing import List, Optional

from llm import router
from llm.backends import initialize
from scripts.cli_common import build_analytics_parser
from scripts import cli_actions
from telemetry import analytics_default

initialize()

RISKY_COMMANDS = {"rm", "reboot", "shutdown", "poweroff", "mkfs", "dd"}


def _label_risk(step: str) -> str:
    """Append a risk tag to ``step`` describing potential danger."""
    try:
        tokens = shlex.split(step)
    except ValueError:
        return f"{step} [risk:info]"
    if not tokens:
        return f"{step} [risk:info]"
    cmd = tokens[0]
    risk = "info"
    if cmd == "sudo":
        risk = "sudo"
        if len(tokens) > 1 and tokens[1] in RISKY_COMMANDS:
            risk = tokens[1]
    elif cmd in RISKY_COMMANDS:
        risk = cmd
    return f"{step} [risk:{risk}]"


def suggest(
    goal: str,
    *,
    local: bool = False,
    model: str = router.DEFAULT_MODEL,
    context: str | None = None,
) -> List[str]:
    """Return up to three risk-tagged shell command suggestions for ``goal``."""
    text = router.shell_suggest(goal, local=local, model=model, context=context)
    return [_label_risk(line) for line in text[:3]]


def main(argv: Optional[List[str]] = None) -> int:
    analytics = build_analytics_parser()
    parser = argparse.ArgumentParser(description=__doc__, parents=[analytics])
    parser.add_argument("goal", help="High level description of the task")
    parser.add_argument("--local", action="store_true", help="Force use of fallback backend")
    parser.add_argument(
        "--model",
        default=router.DEFAULT_MODEL,
        help="Model name for Ollama (default: %(default)s)",
    )
    args = parser.parse_args(argv)
    args.analytics = getattr(args, "analytics", analytics_default())
    try:
        suggestions = suggest(args.goal, local=args.local, model=args.model)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(exc, file=sys.stderr)
        cli_actions.record_event_logged(
            "ai-suggest", {"exit_code": 1}, enabled=args.analytics
        )
        return 1
    for line in suggestions:
        print(line)
    cli_actions.record_event_logged(
        "ai-suggest",
        {"exit_code": 0, "suggestion_count": len(suggestions)},
        enabled=args.analytics,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
