"""Git recipe plug-in."""
from __future__ import annotations

from typing import List

from llm.backends.plugin_sdk import register_recipe


def run(_: str) -> List[str]:
    """Install Git via winget."""
    return ["winget install -e --id Git.Git"]


register_recipe("git", run)

__all__ = ["run"]
