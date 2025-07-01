#!/usr/bin/env python3
"""Simple AI execution planner using ``ai_router``."""


from __future__ import annotations

import argparse
import subprocess
from typing import List, Optional

from scripts import ai_router
from llm.ai_router import get_preferred_models


def plan(goal: str, *, config_path: Optional[str] = None) -> List[str]:
    """Return planning steps for ``goal`` using preferred models."""
    primary, fallback = get_preferred_models(
        ai_router.DEFAULT_MODEL, ai_router.DEFAULT_MODEL, config_path=config_path
    )
    try:
        text = ai_router.run_gemini(goal, model=primary)
    except (FileNotFoundError, subprocess.CalledProcessError):
        text = ai_router.run_ollama(goal, model=fallback)
    return [line.strip() for line in text.splitlines() if line.strip()]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("goal")
    parser.add_argument("--config")
    args = parser.parse_args(argv)
    steps = plan(args.goal, config_path=args.config)
    for step in steps:
        print(step)
    return 0



if __name__ == "__main__":
    raise SystemExit(main())
