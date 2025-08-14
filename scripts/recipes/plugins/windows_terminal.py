"""Windows Terminal recipe plug-in."""
from __future__ import annotations

from typing import List

from llm.backends.plugin_sdk import register_recipe


def run(_: str) -> List[str]:
    """Install Windows Terminal via winget."""
    return ["winget install -e --id Microsoft.WindowsTerminal"]


register_recipe("windows_terminal", run)

__all__ = ["run"]
