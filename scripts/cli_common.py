"""Utilities shared by various command-line interfaces.

These helpers provide common functionality for reading prompts from
``STDIN``, executing interactive shell steps with logging, posting
notifications and building analytics argument parsers.
"""
from __future__ import annotations

import argparse
import os
import secrets
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional, Set

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
    capabilities: Set[str] = field(default_factory=set)


_SESSION_TOKENS: dict[str, str] = {}
SESSION_LOG = Path(os.environ.get("SESSION_LOG", "session.log"))


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
    allowed_capabilities: Set[str] | None = None,
    dry_run_log: list[str] | None = None,
) -> int:
    """Execute ``steps`` and write a log to ``log_path``.

    ``dry_run`` prints the planned commands and their diffs without executing
    them. When executing, commands tagged with ``[risk:*]`` require the
    ``confirm`` flag to be set or the function aborts before running anything.
    """
    step_list = list(steps)

    if dry_run:
        lines: list[str] = []
        for step in step_list:
            line = f"{step.number}. {step.command}"
            print(line)
            lines.append(line)
            if step.diff:
                print(step.diff)
                lines.append(step.diff)
        for step in step_list:
            with log_path.open("a", encoding="utf-8") as log:
                log.write(f"$ {step.command}\n")
                if step.diff:
                    log.write(f"{step.diff}\n")
                log.write(f"[capabilities: {', '.join(sorted(step.capabilities))}]\n")
                log.write("(dry-run)\n\n")
        if dry_run_log is not None:
            dry_run_log.extend(lines)
        return 0

    risk_present = any("[risk:" in step.command for step in step_list)

    if dry_run_log:
        for line in dry_run_log:
            print(line)
        if risk_present and not confirm:
            print(
                "Risky commands present. Re-run with --confirm to execute.",
                file=sys.stderr,
            )
            return 1
        if not (assume_yes or confirm):
            answer = input("Proceed with execution? [y/N]").strip().lower()
            if answer != "y":
                return 1
    elif risk_present and not confirm:
        print(
            "Risky commands present. Re-run with --confirm to execute.",
            file=sys.stderr,
        )
        return 1

    exit_code = 0
    allowed = set(allowed_capabilities) if allowed_capabilities else set()


    for step in step_list:
        if not dry_run_log:
            print(f"{step.number}. {step.command}")
            if step.diff:
                print(step.diff)

        missing_caps = step.capabilities - allowed
        if missing_caps:
            skip_step = False
            for cap in sorted(missing_caps):
                cap_name = cap.value if hasattr(cap, "value") else str(cap)
                if cap_name in _SESSION_TOKENS:
                    token = _SESSION_TOKENS[cap_name]
                    allowed.add(cap_name)
                    with log_path.open("a", encoding="utf-8") as log:
                        log.write(f"[using capability token: {cap_name}={token}]\n")
                    continue
                answer = input(f"Grant capability {cap_name}? [y/N]").strip().lower()

                if answer == "y":
                    token = secrets.token_hex(8)
                    _SESSION_TOKENS[cap_name] = token
                    allowed.add(cap_name)
                    with log_path.open("a", encoding="utf-8") as log:
                        log.write(f"[granted capability: {cap_name} token={token}]\n")
                    SESSION_LOG.parent.mkdir(parents=True, exist_ok=True)
                    with SESSION_LOG.open("a", encoding="utf-8") as slog:
                        slog.write(
                            f"[granted capability: {cap_name} token={token}]\n"
                        )
                else:
                    msg = f"Missing capabilities: {cap_name}"
                    print(msg, file=sys.stderr)
                    with log_path.open("a", encoding="utf-8") as log:
                        log.write(f"$ {step.command}\n")
                        log.write(f"[missing capabilities: {cap_name}]\n")

                        log.write("(skipped)\n\n")
                    SESSION_LOG.parent.mkdir(parents=True, exist_ok=True)
                    with SESSION_LOG.open("a", encoding="utf-8") as slog:
                        slog.write(f"[denied capability: {cap_name}]\n")
                    if not exit_code:
                        exit_code = 1
                    skip_step = True
                    break
            if skip_step:
                continue
        step_assume_yes = assume_yes or confirm

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
            log.write(
                f"[capabilities: {', '.join(sorted(step.capabilities))}]\n"
            )
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
