#!/usr/bin/env python3
"""Simple AI execution planner using the router utilities."""


from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import List, Optional
from threading import Lock

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

_LAST_MODEL_REMOTE = True
_LAST_MODEL_LOCK = Lock()

def last_model_remote() -> bool:
    """Return ``True`` if the last plan used a remote model."""
    with _LAST_MODEL_LOCK:
        return _LAST_MODEL_REMOTE

load_backends()

def plan(
    goal: str, *, config_path: Optional[Path] = None, analytics: bool = False
) -> List[str]:
    """Return planning steps for ``goal`` using preferred models."""
    global _LAST_MODEL_REMOTE
    start = time.time()
    primary, fallback = get_preferred_models(
        router.DEFAULT_MODEL, router.DEFAULT_MODEL, config_path=config_path

    )
    used_remote = True
    exit_code = 0
    steps: List[str] = []
    try:
        try:
            text = router.run_gemini(goal, model=primary)
        except (FileNotFoundError, subprocess.CalledProcessError):
            used_remote = False
            text = router.run_ollama(goal, model=fallback or router.DEFAULT_MODEL)

        steps = [line.strip() for line in text.splitlines() if line.strip()]
        return steps
    except Exception:
        exit_code = 1
        raise
    finally:
        end = time.time()
        with _LAST_MODEL_LOCK:
            _LAST_MODEL_REMOTE = used_remote
        record_event(
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
