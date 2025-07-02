#!/usr/bin/env python3
"""Simple AI execution planner using the router utilities."""


from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import List, Optional, cast

from llm import router
from llm.ai_router import get_preferred_models


def plan(goal: str, *, config_path: Optional[str] = None) -> List[str]:
    """Return planning steps for ``goal`` using preferred models."""
    path = Path(config_path) if config_path else None
    primary, fallback = get_preferred_models(
        router.DEFAULT_MODEL, router.DEFAULT_MODEL, config_path=path
    )
    try:
        text = router.run_gemini(goal, model=primary)
    except (FileNotFoundError, subprocess.CalledProcessError):
        text = router.run_ollama(goal, model=cast(str, fallback))

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
