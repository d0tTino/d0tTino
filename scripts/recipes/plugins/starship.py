"""Starship recipe plug-in."""
from __future__ import annotations

from typing import List

from llm.backends.plugin_sdk import register_recipe


def run(_: str) -> List[str]:
    """Install the Starship prompt via winget."""
    return ["winget install -e --id Starship.Starship"]


register_recipe("starship", run)

__all__ = ["run"]
