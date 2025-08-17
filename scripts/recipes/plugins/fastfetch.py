"""Fastfetch recipe plug-in."""
from __future__ import annotations

from typing import List

from llm.backends.plugin_sdk import register_recipe


def run(_: str) -> List[str]:
    """Install Fastfetch via winget."""
    return ["winget install -e --id Fastfetch.Fastfetch"]


register_recipe("fastfetch", run)

__all__ = ["run"]
