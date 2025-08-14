"""Docker Desktop recipe plug-in."""
from __future__ import annotations

from typing import List

from llm.backends.plugin_sdk import register_recipe


def run(_: str) -> List[str]:
    """Install Docker Desktop using winget."""
    return ["winget install -e --id Docker.DockerDesktop"]


register_recipe("docker_desktop", run)

__all__ = ["run"]
