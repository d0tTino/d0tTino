"""Shared runtime state for the :mod:`scripts.tino_cli` command line."""

from __future__ import annotations

import getpass
import os
import platform
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping


def stable_dict(data: Mapping[str, Any]) -> dict[str, Any]:
    """Return a dictionary with keys sorted for stable JSON output."""

    return {key: data[key] for key in sorted(data)}


def snapshot_identity() -> dict[str, str]:
    """Capture user and host identity information once per CLI session."""

    identity: dict[str, str] = {}
    for key in ("USER", "USERNAME", "LOGNAME"):
        value = os.environ.get(key)
        if value:
            identity[key] = value

    hostname = os.environ.get("HOSTNAME") or os.environ.get("COMPUTERNAME") or platform.node()
    if hostname:
        identity["HOSTNAME"] = hostname

    try:
        system_user = getpass.getuser()
    except Exception:  # pragma: no cover - fallback when system lookup fails
        system_user = None
    if system_user and system_user not in identity.values():
        identity["SYSTEM_USER"] = system_user

    return stable_dict(identity)


@dataclass(slots=True)
class CLIState:
    """Per-invocation CLI state stored on :class:`typer.Context` objects."""

    dry_run: bool
    confirm: bool
    telemetry_enabled: bool
    log_path: Path
    identity: Mapping[str, str] = field(default_factory=dict)
    services: Mapping[str, str] = field(default_factory=dict)


__all__ = ["CLIState", "snapshot_identity", "stable_dict"]
