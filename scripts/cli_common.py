"""Shared utilities for CLI modules."""
from __future__ import annotations

import os
import shlex
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Iterable

import requests


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


def analytics_default() -> bool:
    """Return ``True`` when ``EVENTS_ENABLED`` is set to a truthy value."""
    val = os.environ.get("EVENTS_ENABLED")
    return str(val).lower() in {"1", "true", "yes", "y"}


def record_event(name: str, payload: dict, *, enabled: bool = False) -> None:
    """Send ``payload`` to ``EVENTS_URL`` when ``enabled`` is ``True``."""
    if not enabled:
        return
    url = os.environ.get("EVENTS_URL")
    if not url:
        return
    token = os.environ.get("EVENTS_TOKEN")
    headers = {}
    if token:
        headers["apikey"] = token
        headers["Authorization"] = f"Bearer {token}"
    dev_src = (
        os.environ.get("GIT_AUTHOR_EMAIL")
        or os.environ.get("EMAIL")
        or os.environ.get("USER")
        or "unknown"
    )
    developer = uuid.uuid5(uuid.NAMESPACE_DNS, dev_src).hex
    data = {"name": name, "developer": developer, **payload}
    try:
        requests.post(url, headers=headers, json=data, timeout=5)
    except Exception:
        pass


__all__ = [
    "read_prompt",
    "execute_steps",
    "send_notification",
    "analytics_default",
    "record_event",
]
