"""Shared runtime state for the :mod:`scripts.tino_cli` command line."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class CLIState:
    """Per-invocation CLI state stored on :class:`typer.Context` objects."""

    dry_run: bool
    confirm: bool
    telemetry_enabled: bool
    log_path: Path


__all__ = ["CLIState"]
