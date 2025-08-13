"""Utilities shared by various command-line interfaces.

These helpers provide common functionality for reading prompts from
``STDIN``, executing interactive shell steps with logging, posting
notifications and building analytics argument parsers.
"""
from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import requests  # noqa: F401 -- imported for backward-compatibility
from telemetry import analytics_default, record_event


def read_prompt(prompt: str) -> str:
    """Return ``prompt`` or read from ``STDIN`` if ``prompt`` is '-'."""
    if prompt == "-":
        return sys.stdin.read()
    return prompt


@dataclass
class PlanStep:
    """Single planned step with an optional diff preview."""

    number: int
    command: str
    diff: Optional[str] = None


def _strip_risk_tag(command: str) -> str:
    """Return ``command`` without any ``[risk:*]`` suffix."""

    if " [risk:" in command:
        return command.rsplit(" [risk:", 1)[0]
    return command


def execute_steps(
    steps: Iterable[PlanStep],
    *,
    log_path: Path,
    dry_run: bool = False,
    assume_yes: bool = False,
    confirm: bool = False,
) -> int:
    """Execute ``steps`` and write a log to ``log_path``.

    When ``dry_run`` is ``True`` the commands are printed and logged without
    being executed. If ``assume_yes`` is ``True`` all confirmation prompts are
    skipped for non-risky commands. Commands tagged with ``[risk:*]`` require the
    ``confirm`` flag to run without prompting.
    """
    exit_code = 0
    for step in steps:
        is_risky = "[risk:" in step.command
        step_assume_yes = assume_yes and (confirm or not is_risky)
        if dry_run:
            print(f"{step.number}. {step.command}")
            if step.diff:
                print(step.diff)
            with log_path.open("a", encoding="utf-8") as log:
                log.write(f"$ {step.command}\n")
                if step.diff:
                    log.write(f"{step.diff}\n")
                log.write("(dry-run)\n\n")
            continue

        if not step_assume_yes:
            answer = input(f"{step.number}. {step.command} [y/N]?").strip().lower()
            if answer != "y":
                continue
        else:
            print(f"{step.number}. {step.command}")

        cmd_text = _strip_risk_tag(step.command)
        try:
            tokens = shlex.split(cmd_text)
        except ValueError:
            tokens = []
            needs_shell = True
        else:
            special_chars = any(ch in cmd_text for ch in "|&;><$`")
            if os.name == "nt":
                # ``shlex.join`` uses POSIX quoting which breaks on Windows.
                needs_shell = special_chars
            else:
                needs_shell = special_chars or shlex.join(tokens) != cmd_text
        cmd = cmd_text if needs_shell else tokens
        cmd_str = cmd_text if needs_shell else " ".join(tokens)
        if not step_assume_yes:
            answer = input(f"Run command: {cmd_str} [y/N]?").strip().lower()
            if answer != "y":
                continue
        else:
            print(f"$ {cmd_str}")
        result = subprocess.run(cmd, shell=needs_shell, capture_output=True, text=True)
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"$ {step.command}\n")
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
    "PlanStep",
]
