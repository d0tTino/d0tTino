"""WSL recipe plug-in."""
from __future__ import annotations

from typing import List

from llm.backends.plugin_sdk import register_recipe


def run(_: str) -> List[str]:
    """Install the Windows Subsystem for Linux."""
    return ["wsl --install"]


register_recipe("wsl", run)

__all__ = ["run"]
