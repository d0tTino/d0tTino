"""Node.js recipe plug-in."""
from __future__ import annotations

from typing import List

from llm.backends.plugin_sdk import register_recipe


def run(_: str) -> List[str]:
    """Install Node.js via winget."""
    return ["winget install -e --id OpenJS.NodeJS.LTS"]


register_recipe("nodejs", run)

__all__ = ["run"]
