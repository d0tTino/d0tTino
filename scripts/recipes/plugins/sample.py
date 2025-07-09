"""Sample recipe plug-in."""
from __future__ import annotations

from typing import List

from llm.backends.plugin_sdk import register_recipe


def run(goal: str) -> List[str]:
    """Return a simple command echoing the goal."""
    return [f"echo {goal}"]

register_recipe("sample", run)

__all__ = ["run"]
