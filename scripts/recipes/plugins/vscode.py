"""VS Code recipe plug-in."""
from __future__ import annotations

from typing import List
from pathlib import Path

from llm.backends.plugin_sdk import register_recipe

CONFIG = (Path(__file__).resolve().parent.parent / "config" / "vscode.yaml").as_posix()


def run(_: str) -> List[str]:
    """Install Visual Studio Code and common extensions."""
    return [
        f"winget configure -f {CONFIG}",
        "code --install-extension ms-python.python",
        "code --install-extension ms-toolsai.jupyter",
    ]


register_recipe("vscode", run)

__all__ = ["run"]
