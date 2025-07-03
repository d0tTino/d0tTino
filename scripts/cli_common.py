"""Shared utilities for CLI modules."""
from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable


def read_prompt(prompt: str) -> str:
    """Return ``prompt`` or read from ``STDIN`` if ``prompt`` is '-'."""
    if prompt == "-":
        return sys.stdin.read()
    return prompt


def execute_steps(
    steps: Iterable[str], *, log_path: Path, notify_topic: str | None = None
) -> int:
    """Interactively execute ``steps`` and write a log to ``log_path``.

    If ``notify_topic`` is provided, each executed or skipped step publishes its
    status to ``notify_topic/step-N`` using :func:`send_notification`.
    """
    exit_code = 0
    for i, step in enumerate(steps, 1):
        answer = input(f"{i}. {step} [y/N]?").strip().lower()
        if answer != "y":
            if notify_topic:
                send_notification(
                    "skipped", topic=f"{notify_topic}/step-{i}"
                )
            continue
        tokens = shlex.split(step)
        needs_shell = any(ch in step for ch in "|&;><$`")
        cmd = step if needs_shell else tokens
        cmd_str = step if needs_shell else " ".join(tokens)
        answer = input(f"Run command: {cmd_str} [y/N]?").strip().lower()
        if answer != "y":
            if notify_topic:
                send_notification(
                    "skipped", topic=f"{notify_topic}/step-{i}"
                )
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
        if notify_topic:
            status = "success" if result.returncode == 0 else f"failed ({result.returncode})"
            send_notification(status, topic=f"{notify_topic}/step-{i}")
        if result.returncode and not exit_code:
            exit_code = result.returncode
    return exit_code


def send_notification(message: str, *, topic: str | None = None) -> None:
    """Post ``message`` via ``ntfy`` if available.

    If ``topic`` is given, the message is published to ``https://ntfy.sh/<topic>``
    using ``curl``. Otherwise the local ``ntfy`` client is invoked.
    """
    if topic:
        subprocess.run(["curl", "-sS", "-d", message, f"https://ntfy.sh/{topic}"], check=False)
    else:
        subprocess.run(["ntfy", "send", message], check=False)


__all__ = ["read_prompt", "execute_steps", "send_notification"]
