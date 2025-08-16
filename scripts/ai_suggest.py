#!/usr/bin/env python3
"""Suggest up to three shell commands for a goal with risk labels."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

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


def _split_rationale(line: str) -> tuple[str, str]:
    """Split ``line`` into ``command`` and ``rationale`` parts."""
    if " # " in line:
        cmd, rationale = line.split(" # ", 1)
        return cmd.strip(), rationale.strip()
    return line.strip(), ""


def suggest(
    goal: str,
    *,
    local: bool = False,
    model: str = router.DEFAULT_MODEL,
    context: str | None = None,
) -> List[Dict[str, str]]:
    """Return up to three risk-tagged suggestions with rationales."""
    prompt = f"{goal}\nExplain each command briefly"
    text = router.shell_suggest(prompt, local=local, model=model, context=context)
    suggestions: List[Dict[str, str]] = []
    for line in text[:3]:
        cmd, rationale = _split_rationale(line)
        suggestions.append({"command": _label_risk(cmd), "rationale": rationale})
    return suggestions


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
    parser.add_argument("--json", action="store_true", help="Output suggestions as JSON")
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
    if args.json:
        print(json.dumps(suggestions))
    else:
        log_path = Path.home() / ".config" / "d0tTino" / "ai_suggest.log"
        for idx, item in enumerate(suggestions, 1):
            print(item["command"])
            if item["rationale"]:
                print(item["rationale"])
            answer = input("Press Enter to run, anything else to skip: ").strip()
            if answer == "":
                cli_actions.run_steps(
                    "ai-suggest-run",
                    [item["command"]],
                    log_path=log_path,
                    analytics=args.analytics,
                    assume_yes=True,
                    confirm=True,
                    payload={"suggestion_index": idx, "goal": args.goal},
                )
    cli_actions.record_event_logged(
        "ai-suggest",
        {"exit_code": 0, "suggestion_count": len(suggestions)},
        enabled=args.analytics,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
