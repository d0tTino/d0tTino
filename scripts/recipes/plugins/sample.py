"""Sample recipe plug-in."""
from __future__ import annotations

from typing import List


def run(goal: str) -> List[str]:
    """Return a simple command echoing the goal."""
    return [f"echo {goal}"]

__all__ = ["run"]
