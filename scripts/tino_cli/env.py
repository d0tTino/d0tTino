"""Environment loading utilities."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

_REPO_ROOT = Path(__file__).resolve().parents[2]


def iter_env_lines(path: Path) -> Iterable[tuple[str, str]]:
    """Yield key/value pairs parsed from ``path``."""

    if not path.exists():
        return []
    pairs: list[tuple[str, str]] = []
    for line in path.read_text().splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        if "=" not in text:
            continue
        key, value = text.split("=", 1)
        pairs.append((key.strip(), value.strip()))
    return pairs


def load_env() -> None:
    """Populate ``os.environ`` with settings from ``.env`` if missing."""

    for key, value in iter_env_lines(_REPO_ROOT / ".env"):
        os.environ.setdefault(key, value)


__all__ = ["load_env", "_REPO_ROOT"]
