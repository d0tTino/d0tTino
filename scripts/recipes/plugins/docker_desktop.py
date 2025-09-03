"""Docker Desktop recipe plug-in."""
from __future__ import annotations

from typing import List
from pathlib import Path

from llm.backends.plugin_sdk import register_recipe

CONFIG = (Path(__file__).resolve().parent.parent / "config" / "docker_desktop.yaml").as_posix()


def run(_: str) -> List[str]:
    """Install Docker Desktop and configure the WSL 2 backend."""
    return [
        f"winget configure -f {CONFIG}",
        "wsl --set-default-version 2",
    ]


register_recipe("docker_desktop", run)

__all__ = ["run"]
