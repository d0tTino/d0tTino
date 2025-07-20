"""Shared utilities for CLI modules."""
from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable

import requests  # noqa: F401 -- imported for backward-compatibility
from telemetry import analytics_default, record_event


def read_prompt(prompt: str) -> str:
    """Return ``prompt`` or read from ``STDIN`` if ``prompt`` is '-'."""
    if prompt == "-":
        return sys.stdin.read()
    return prompt


def execute_steps(steps: Iterable[str], *, log_path: Path) -> int:
    """Interactively execute ``steps`` and write a log to ``log_path``."""
    exit_code = 0
    for i, step in enumerate(steps, 1):
        answer = input(f"{i}. {step} [y/N]?").strip().lower()
        if answer != "y":
            continue
        try:
            tokens = shlex.split(step)
        except ValueError:
            tokens = []
            needs_shell = True
        else:
            special_chars = any(ch in step for ch in "|&;><$`")
            if os.name == "nt":
                # ``shlex.join`` uses POSIX quoting which breaks on Windows.
                needs_shell = special_chars
            else:
                needs_shell = special_chars or shlex.join(tokens) != step
        cmd = step if needs_shell else tokens
        cmd_str = step if needs_shell else " ".join(tokens)
        answer = input(f"Run command: {cmd_str} [y/N]?").strip().lower()
        if answer != "y":
            continue
        result = subprocess.run(cmd, shell=needs_shell, capture_output=True, text=True)
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"$ {step}\n")
            if result.stdout:
                log.write(result.stdout)
            if result.stderr:
                log.write(result.stderr)
            log.write(f"(exit {result.returncode})\n\n")
        print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        if result.returncode and not exit_code:
            exit_code = result.returncode
    return exit_code


def send_notification(message: str) -> None:
    """Post ``message`` via ``ntfy`` if available."""
    subprocess.run(["ntfy", "send", message], check=False)


def build_analytics_parser() -> argparse.ArgumentParser:
    """Return an argument parser handling the ``--analytics`` flag."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--analytics",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Record anonymous usage events",
    )
    return parser




__all__ = [
    "read_prompt",
    "execute_steps",
    "send_notification",
    "build_analytics_parser",
    "analytics_default",
    "record_event",
]
