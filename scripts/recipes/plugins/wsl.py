"""WSL recipe plug-in."""
from __future__ import annotations

from typing import List
from pathlib import Path

from llm.backends.plugin_sdk import register_recipe

CONFIG = (Path(__file__).resolve().parent.parent / "config" / "wsl.yaml").as_posix()


def run(_: str) -> List[str]:
    """Install the Windows Subsystem for Linux via winget."""
    return [
        f"winget configure -f {CONFIG}",
        "wsl --set-default-version 2",
    ]


register_recipe("wsl", run)

__all__ = ["run"]
