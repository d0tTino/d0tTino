#!/usr/bin/env python3
"""Simple AI execution planner using the router utilities."""


from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import List, Optional

from llm import router
from llm.ai_router import get_preferred_models


def send_notification(message: str) -> None:
    """Post a notification via ``ntfy`` if available."""
    subprocess.run(["ntfy", "send", message], check=False)


def plan(goal: str, *, config_path: Optional[Path] = None) -> List[str]:
    """Return planning steps for ``goal`` using preferred models."""
    primary, fallback = get_preferred_models(
        router.DEFAULT_MODEL, router.DEFAULT_MODEL, config_path=config_path

    )
    try:
        text = router.run_gemini(goal, model=primary)
    except (FileNotFoundError, subprocess.CalledProcessError):
        text = router.run_ollama(goal, model=fallback or router.DEFAULT_MODEL)

    return [line.strip() for line in text.splitlines() if line.strip()]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("goal")
    parser.add_argument("--config")
    parser.add_argument("--notify", action="store_true", help="Send notification when done")
    args = parser.parse_args(argv)
    cfg_path = Path(args.config) if args.config else None
    steps = plan(args.goal, config_path=cfg_path)
    for step in steps:
        print(step)
    if args.notify:
        send_notification("ai-plan completed")
    return 0



if __name__ == "__main__":
    raise SystemExit(main())
