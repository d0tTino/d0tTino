"""Shared command execution helpers for :mod:`scripts.tino_cli`."""
from __future__ import annotations

from collections.abc import Iterable
import shlex
import subprocess

import typer

from .state import CLIState


def _normalise_command(command: Iterable[str] | str) -> list[str]:
    if isinstance(command, str):
        return shlex.split(command)
    return list(command)


def execute_command(
    command: Iterable[str] | str,
    *,
    state: CLIState | None = None,
    require_confirm: bool = False,
) -> int:
    """Execute ``command`` honouring the active CLI ``state`` semantics."""

    command_list = _normalise_command(command)
    printable = " ".join(shlex.quote(arg) for arg in command_list)
    if state is not None and state.dry_run:
        typer.echo(f"[dry-run] {printable}")
        return 0
    if require_confirm and (state is None or not state.confirm):
        typer.echo("Use --confirm to execute this command.", err=True)
        return 1
    return subprocess.call(command_list)


__all__ = ["execute_command"]
