"""Deploy recipe plug-in."""
from __future__ import annotations

from typing import List

from llm.backends.plugin_sdk import register_recipe


def run(goal: str) -> List[str]:
    """Return a command that echoes the deploy goal."""
    return [f"echo deploy {goal}"]


register_recipe("deploy", run)

__all__ = ["run"]
