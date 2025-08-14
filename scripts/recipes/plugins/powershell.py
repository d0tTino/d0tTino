"""PowerShell recipe plug-in."""
from __future__ import annotations

from typing import List

from llm.backends.plugin_sdk import register_recipe


def run(_: str) -> List[str]:
    """Install PowerShell via winget."""
    return ["winget install -e --id Microsoft.PowerShell"]


register_recipe("powershell", run)

__all__ = ["run"]
