"""VS Code recipe plug-in."""
from __future__ import annotations

from typing import List

from llm.backends.plugin_sdk import register_recipe


def run(_: str) -> List[str]:
    """Install Visual Studio Code and common extensions."""
    return [
        "winget install -e --id Microsoft.VisualStudioCode",
        "code --install-extension ms-python.python",
        "code --install-extension ms-toolsai.jupyter",
    ]


register_recipe("vscode", run)

__all__ = ["run"]
