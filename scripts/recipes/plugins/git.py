"""Git recipe plug-in."""
from __future__ import annotations

from typing import List
from pathlib import Path

from llm.backends.plugin_sdk import register_recipe

CONFIG = (Path(__file__).resolve().parent.parent / "config" / "git.yaml").as_posix()


def run(_: str) -> List[str]:
    """Install Git via winget."""
    return [f"winget configure -f {CONFIG}"]


register_recipe("git", run)

__all__ = ["run"]
