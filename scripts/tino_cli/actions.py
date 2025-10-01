"""Handlers for cockpit automation commands."""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

from telemetry import record_event

from .models import ActionSpec, CommandResult
from .utils import ensure_cache_dir, telemetry_status


@dataclass(slots=True)
class ActionStep:
    """Represent a shell command to execute."""

    index: int
    command: str


DEFAULT_ACTIONS: dict[str, ActionSpec] = {
    "cockpit-up": ActionSpec(
        name="cockpit-up",
        description="Start the local automation services",
        steps=("echo starting automation services",),
    ),
    "cockpit-down": ActionSpec(
        name="cockpit-down",
        description="Stop local automation services",
        steps=("echo stopping automation services",),
        confirm_required=True,
    ),
    "cockpit-new-task": ActionSpec(
        name="cockpit-new-task",
        description="Register a new task for execution",
        steps=("echo registering new task: {payload}",),
    ),
    "cockpit-inject-context": ActionSpec(
        name="cockpit-inject-context",
        description="Inject additional context into the agent",
        steps=("echo context injected: {payload}",),
        log_name="context.log",
    ),
    "cockpit-research-ingest": ActionSpec(
        name="cockpit-research-ingest",
        description="Trigger the research ingestion pipeline",
        steps=("echo ingesting research from {payload}",),
    ),
    "cockpit-wishlist-add": ActionSpec(
        name="cockpit-wishlist-add",
        description="Add an item to the wishlist",
        steps=("echo wishlist item added: {payload}",),
    ),
    "cockpit-publish-docs": ActionSpec(
        name="cockpit-publish-docs",
        description="Publish generated documentation",
        steps=("echo publishing documentation",),
        confirm_required=True,
    ),
}


def _render_steps(spec: ActionSpec, payload: str | None) -> List[ActionStep]:
    rendered: List[ActionStep] = []
    for idx, raw in enumerate(spec.steps, start=1):
        rendered.append(ActionStep(idx, raw.format(payload=payload or "")))
    return rendered


def _shell_command(command: str) -> List[str]:
    if os.name == "nt":
        return ["cmd", "/C", command]
    return ["/bin/sh", "-c", command]


def _execute_steps(steps: Iterable[ActionStep], log_path: os.PathLike[str]) -> tuple[int, list[str]]:
    log_entries: list[str] = []
    exit_code = 0
    with open(log_path, "w", encoding="utf-8") as handle:
        for step in steps:
            handle.write(f"$ {step.command}\n")
            proc = subprocess.run(
                _shell_command(step.command),
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.stdout:
                handle.write(proc.stdout)
            if proc.stderr:
                handle.write(proc.stderr)
            exit_code = proc.returncode
            handle.write(f"(exit {exit_code})\n\n")
            log_entries.append(step.command)
    return exit_code, log_entries


def run_action(name: str, *, payload: str | None = None, confirm: bool = False) -> CommandResult:
    """Execute a cockpit action described by ``name``."""

    spec = DEFAULT_ACTIONS.get(name)
    if not spec:
        raise ValueError(f"Unknown action: {name}")
    if spec.confirm_required and not confirm:
        raise PermissionError("confirmation-required")

    cache_dir = ensure_cache_dir()
    log_path = spec.log_path(cache_dir)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    steps = _render_steps(spec, payload)
    exit_code, rendered_commands = _execute_steps(steps, log_path)

    timestamp = time.time()
    audit_path = cache_dir / "cockpit.log"
    entry = {
        "timestamp": timestamp,
        "action": name,
        "payload": payload,
        "exit_code": exit_code,
    }
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")

    telemetry = telemetry_status()
    if telemetry.enabled:
        record_event(
            name,
            {
                "exit_code": exit_code,
                "payload": payload,
                "timestamp": timestamp,
            },
            enabled=True,
        )

    details: Dict[str, Any] = {
        "log_path": str(log_path),
        "audit_path": str(audit_path),
        "exit_code": exit_code,
        "commands": rendered_commands,
    }
    if payload:
        details["payload"] = payload
    message = f"{spec.description} (exit {exit_code})"
    return CommandResult(message=message, telemetry=telemetry, details=details)


def tail_logs(limit: int = 200) -> dict[str, Any]:
    """Return the most recent cockpit log entries."""

    cache_dir = ensure_cache_dir()
    path = cache_dir / "cockpit.log"
    entries: list[dict[str, Any]] = []
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            lines = handle.readlines()[-limit:]
        for line in lines:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return {"entries": entries, "path": str(path)}


def run_commands(commands: Iterable[str], log_path: os.PathLike[str]) -> tuple[int, list[str]]:
    """Execute ``commands`` and persist their output to ``log_path``."""

    steps = [ActionStep(idx + 1, cmd) for idx, cmd in enumerate(commands)]
    return _execute_steps(steps, log_path)


__all__ = ["DEFAULT_ACTIONS", "run_action", "tail_logs", "ActionStep", "run_commands"]
