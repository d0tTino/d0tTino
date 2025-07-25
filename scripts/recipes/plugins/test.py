"""Test recipe plug-in."""
from __future__ import annotations

from typing import List

from llm.backends.plugin_sdk import register_recipe


def run(goal: str) -> List[str]:
    """Return a command that echoes the test goal."""
    return [f"echo test {goal}"]


register_recipe("test", run)

__all__ = ["run"]
