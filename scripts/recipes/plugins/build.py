"""Build recipe plug-in."""
from __future__ import annotations

from typing import List

from llm.backends.plugin_sdk import register_recipe


def run(goal: str) -> List[str]:
    """Return a command that echoes the build goal."""
    return [f"echo build {goal}"]


register_recipe("build", run)

__all__ = ["run"]
