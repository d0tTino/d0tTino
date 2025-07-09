#!/usr/bin/env python3
"""Simple AI execution planner using the router utilities."""


from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import List, Optional

from llm import router
from llm.ai_router import get_preferred_models
from llm.backends import load_backends
from scripts.cli_common import (
    read_prompt,
    record_event,
    send_notification,
    analytics_default,
)
import time

load_backends()

def plan(
    goal: str, *, config_path: Optional[Path] = None, analytics: bool = False
) -> List[str]:
    """Return planning steps for ``goal`` using preferred models."""
    start = time.time()
    primary, fallback = get_preferred_models(
        router.DEFAULT_MODEL, router.DEFAULT_MODEL, config_path=config_path

    )
    try:
        text = router.run_gemini(goal, model=primary)
    except (FileNotFoundError, subprocess.CalledProcessError):
        text = router.run_ollama(goal, model=fallback or router.DEFAULT_MODEL)

    steps = [line.strip() for line in text.splitlines() if line.strip()]
    end = time.time()
    record_event(
        "ai-exec-plan",
        {
            "goal": goal,
            "step_count": len(steps),
            "start_ts": start,
            "end_ts": end,
            "latency_ms": int((end - start) * 1000),
        },
        enabled=analytics,
    )
    return steps


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("goal")
    parser.add_argument("--config")
    parser.add_argument("--notify", action="store_true", help="Send notification when done")
    parser.add_argument(
        "--analytics",
        action="store_true",
        help="Record anonymous usage events",
    )
    args = parser.parse_args(argv)
    args.analytics = getattr(args, "analytics", analytics_default())
    cfg_path = Path(args.config) if args.config else None
    goal = read_prompt(args.goal)
    steps = plan(goal, config_path=cfg_path, analytics=args.analytics)
    for step in steps:
        print(step)
    if args.notify:
        send_notification("ai-plan completed")
    return 0



if __name__ == "__main__":
    raise SystemExit(main())
