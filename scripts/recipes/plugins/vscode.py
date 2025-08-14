"""VS Code recipe plug-in."""
from __future__ import annotations

from typing import List

from llm.backends.plugin_sdk import register_recipe


def run(_: str) -> List[str]:
    """Install Visual Studio Code via winget."""
    return ["winget install -e --id Microsoft.VisualStudioCode"]


register_recipe("vscode", run)

__all__ = ["run"]
