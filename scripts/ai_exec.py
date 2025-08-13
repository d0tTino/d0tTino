#!/usr/bin/env python3
"""Simple AI execution planner using the router utilities."""


from __future__ import annotations

import argparse
import shlex
import subprocess
import time
from pathlib import Path
from threading import Lock
from typing import List, Optional

from llm import router
from llm.ai_router import get_preferred_models
from llm.backends import initialize
from scripts.cli_common import (
    PlanStep,
    read_prompt,
    send_notification,
    build_analytics_parser,
)
from scripts import cli_actions
from telemetry import analytics_default

_LAST_MODEL_REMOTE = True
_LAST_MODEL_LOCK = Lock()

RISKY_COMMANDS = {"rm", "reboot", "shutdown", "poweroff", "mkfs", "dd"}


def _tag_risky(step: str) -> str:
    """Append a risk tag with the command type when ``step`` is dangerous."""
    try:
        tokens = shlex.split(step)
    except ValueError:
        return step
    if not tokens:
        return step
    cmd = tokens[0]
    risk: Optional[str] = None
    if cmd == "sudo":
        risk = "sudo"
        if len(tokens) > 1 and tokens[1] in RISKY_COMMANDS:
            risk = tokens[1]
    elif cmd in RISKY_COMMANDS:
        risk = cmd
    if risk:
        return f"{step} [risk:{risk}]"
    return step

def last_model_remote() -> bool:
    """Return ``True`` if the last plan used a remote model."""
    with _LAST_MODEL_LOCK:
        return _LAST_MODEL_REMOTE

initialize()

def _parse_steps(text: str) -> List[PlanStep]:
    """Return a list of :class:`PlanStep` objects from ``text``."""

    steps: List[PlanStep] = []
    current: Optional[str] = None
    diff_lines: List[str] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        if line.startswith((" ", "+", "-", "@", "diff", "---", "+++")) and current:
            diff_lines.append(line)
            continue
        if current is not None:
            steps.append(
                PlanStep(len(steps) + 1, _tag_risky(current), "\n".join(diff_lines) or None)
            )
            diff_lines = []
        current = line.strip()
    if current is not None:
        steps.append(
            PlanStep(len(steps) + 1, _tag_risky(current), "\n".join(diff_lines) or None)
        )
    return steps


def plan(
    goal: str, *, config_path: Optional[Path] = None, analytics: bool = False
) -> List[PlanStep]:
    """Return planning steps for ``goal`` using preferred models."""
    global _LAST_MODEL_REMOTE
    start = time.time()
    primary, fallback = get_preferred_models(
        router.DEFAULT_MODEL, router.DEFAULT_MODEL, config_path=config_path

    )
    used_remote = True
    exit_code = 0
    steps: List[PlanStep] = []
    try:
        try:
            text = router.run_gemini(goal, model=primary)
        except (FileNotFoundError, subprocess.CalledProcessError):
            used_remote = False
            text = router.run_ollama(goal, model=fallback or router.DEFAULT_MODEL)

        steps = _parse_steps(text)
        return steps
    except Exception:
        exit_code = 1
        raise
    finally:
        end = time.time()
        with _LAST_MODEL_LOCK:
            _LAST_MODEL_REMOTE = used_remote
        cli_actions.record_event_logged(
            "ai-exec-plan",
            {
                "goal": goal,
                "exit_code": exit_code,
                "step_count": len(steps),
                "duration_ms": int((end - start) * 1000),
                "model_source": "remote" if used_remote else "local",
            },
            enabled=analytics,
        )


def main(argv: Optional[List[str]] = None) -> int:
    analytics = build_analytics_parser()
    parser = argparse.ArgumentParser(description=__doc__, parents=[analytics])
    parser.add_argument("goal")
    parser.add_argument("--config")
    parser.add_argument("--notify", action="store_true", help="Send notification when done")
    args = parser.parse_args(argv)
    args.analytics = getattr(args, "analytics", analytics_default())
    cfg_path = Path(args.config) if args.config else None
    goal = read_prompt(args.goal)
    steps = plan(goal, config_path=cfg_path, analytics=args.analytics)
    for step in steps:
        print(f"{step.number}. {step.command}")
        if step.diff:
            print(step.diff)
    if args.notify:
        send_notification("ai-plan completed")
    return 0



if __name__ == "__main__":
    raise SystemExit(main())
