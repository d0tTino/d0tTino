"""Configuration helpers for the :mod:`scripts.tino_cli` package."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping
import os
import threading

_ENV_LOADED = False
_ENV_LOCK = threading.Lock()


def _parse_env_lines(lines: Iterable[str]) -> Mapping[str, str]:
    """Return key/value pairs parsed from ``lines`` of a ``.env`` file."""
    result: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        cleaned = value.strip().strip('"').strip("'")
        result[key.strip()] = cleaned
    return result


def load_env_defaults(env_paths: Iterable[Path] | None = None) -> None:
    """Populate :mod:`os.environ` with defaults from ``env_paths``."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    paths = list(env_paths or (Path(".env"), Path(".env.example")))
    with _ENV_LOCK:
        if _ENV_LOADED:
            return
        for path in paths:
            if not path.exists():
                continue
            try:
                values = _parse_env_lines(path.read_text(encoding="utf-8").splitlines())
            except OSError:
                continue
            for key, value in values.items():
                os.environ.setdefault(key, value)
        _ENV_LOADED = True


@dataclass(slots=True)
class ServiceConfig:
    """Runtime configuration for a remote HTTP or WebSocket service."""

    env_var: str
    default_url: str

    def resolve(self) -> str:
        load_env_defaults()
        url = os.environ.get(self.env_var)
        if url:
            return url
        return self.default_url


TASKCASCADENCE = ServiceConfig("TASKCASCADENCE_URL", "http://127.0.0.1:6001")
STORM = ServiceConfig("STORM_URL", "http://127.0.0.1:6002")
UME = ServiceConfig("UME_URL", "http://127.0.0.1:6003")
FINANCE = ServiceConfig("FINANCE_URL", "http://127.0.0.1:6004")
DOCS = ServiceConfig("DOCS_URL", "http://127.0.0.1:6005")

__all__ = [
    "ServiceConfig",
    "TASKCASCADENCE",
    "STORM",
    "UME",
    "FINANCE",
    "DOCS",
    "load_env_defaults",
]
