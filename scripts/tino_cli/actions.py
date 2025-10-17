"""Handlers for cockpit automation commands."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Sequence

from telemetry import record_event

from .main import (
    build_state,
    compose_command,
    docs_publish_operation,
    research_ingest_operation,
    task_run_operation,
    task_signal_operation,
    wishlist_add_operation,
)
from .models import ActionSpec, CommandResult
from .utils import ensure_cache_dir, telemetry_status


@dataclass(slots=True)
class ActionStep:
    """Represent a shell command to execute."""

    index: int
    command: str
    args: Sequence[str] | None = None


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
    if spec.name == "cockpit-up":
        command = compose_command("up", "-d")
        return [ActionStep(1, shlex.join(command), command)]
    if spec.name == "cockpit-down":
        command = compose_command("down")
        return [ActionStep(1, shlex.join(command), command)]
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
            if step.args:
                proc = subprocess.run(
                    list(step.args),
                    capture_output=True,
                    text=True,
                    check=False,
                )
            else:
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


def _invoke_callable(
    log_path: os.PathLike[str],
    command: str,
    call: Callable[[], Any],
) -> tuple[int, list[str], dict[str, Any]]:
    commands = [command]
    details: dict[str, Any] = {}
    exit_code = 0
    with open(log_path, "w", encoding="utf-8") as handle:
        handle.write(f"$ {command}\n")
        try:
            result = call()
        except Exception as exc:  # noqa: BLE001 - bubble up error context
            exit_code = 1
            message = str(exc)
            handle.write(message + "\n")
            details["error"] = message
        else:
            payload = getattr(result, "payload", result)
            if payload is not None:
                try:
                    serialized = json.dumps(payload, indent=2)
                except TypeError:
                    serialized = str(payload)
                handle.write(serialized + "\n")
                details["response"] = payload
        handle.write(f"(exit {exit_code})\n")
    return exit_code, commands, details


def _error_action(log_path: os.PathLike[str], command: str, message: str) -> tuple[int, list[str], dict[str, Any]]:
    commands = [command]
    with open(log_path, "w", encoding="utf-8") as handle:
        handle.write(f"$ {command}\n")
        handle.write(message + "\n")
        handle.write("(exit 1)\n")
    return 1, commands, {"error": message}


def _research_action_payload(raw: str) -> tuple[str | None, str]:
    """Return (topic, source) extracted from ``raw``."""

    source = raw.strip()
    topic: str | None = None
    if "::" in raw:
        topic_part, source_part = raw.split("::", 1)
        source = source_part.strip()
        parsed_topic = topic_part.strip()
        topic = parsed_topic or None
    return topic, source


def _parse_context_payload(job_id: str | None, payload: str | None) -> tuple[str | None, str]:
    """Extract ``job_id`` and ``message`` for context injection."""

    message = (payload or "").strip()
    parsed_job = job_id.strip() if job_id else None
    if not parsed_job and payload and "::" in payload:
        raw_job, raw_message = payload.split("::", 1)
        parsed_job = raw_job.strip() or None
        message = raw_message.strip()
    return parsed_job, message


def _looks_like_url(value: str) -> bool:
    if not value:
        return False
    if value.startswith("http://") or value.startswith("https://"):
        return True
    return False


def _run_special_action(
    name: str,
    payload: str | None,
    confirm: bool,
    log_path: os.PathLike[str],
    *,
    job_id: str | None = None,
) -> tuple[int, list[str], dict[str, Any]]:
    state = build_state(dry_run=False, confirm=confirm)
    if name == "cockpit-new-task":
        if not payload:
            return _error_action(log_path, "task run <missing>", "Task description required.")
        task_name = payload
        command = f"task run {shlex.quote(task_name)}"
        return _invoke_callable(log_path, command, lambda: task_run_operation(state, task_name, payload=None))
    if name == "cockpit-inject-context":
        parsed_job, message = _parse_context_payload(job_id, payload)
        if not parsed_job:
            return _error_action(
                log_path,
                "task signal context <missing>",
                "Task identifier required for context injection.",
            )
        if not message:
            return _error_action(
                log_path,
                "task signal context <missing>",
                "Context message required for injection.",
            )

        is_link = _looks_like_url(message)
        link = message if is_link else None
        note = None if is_link else message

        command = f"task signal context {shlex.quote(parsed_job)}"
        if is_link:
            command += f" --link {shlex.quote(message)}"
        else:
            command += f" --note {shlex.quote(message)}"

        return _invoke_callable(
            log_path,
            command,
            lambda: task_signal_operation(
                state,
                parsed_job,
                signal="context",
                link=link,
                note=note,
            ),
        )
    if name == "cockpit-research-ingest":
        if not payload:
            return _error_action(log_path, "research ingest <missing>", "Source path or URL required.")
        topic, source = _research_action_payload(payload)
        command = f"research ingest {shlex.quote(source)}"
        if topic:
            command += f" --topic {shlex.quote(topic)}"
        return _invoke_callable(
            log_path,
            command,
            lambda: research_ingest_operation(state, source=source, topic=topic),
        )
    if name == "cockpit-wishlist-add":
        if not payload:
            return _error_action(log_path, "wishlist add <missing>", "Wishlist item required.")
        item = payload
        command = f"wishlist add {shlex.quote(item)}"
        return _invoke_callable(log_path, command, lambda: wishlist_add_operation(state, url=item, tags=None))
    if name == "cockpit-publish-docs":
        target = payload or os.environ.get("TINO_DOC_TARGET", "latest")
        command = f"docs publish {shlex.quote(target)}"
        return _invoke_callable(log_path, command, lambda: docs_publish_operation(state, target=target, site=None, version=None))
    raise ValueError(f"Unknown action: {name}")


def run_action(
    name: str,
    *,
    payload: str | None = None,
    confirm: bool = False,
    job_id: str | None = None,
) -> CommandResult:
    """Execute a cockpit action described by ``name``."""

    spec = DEFAULT_ACTIONS.get(name)
    if not spec:
        raise ValueError(f"Unknown action: {name}")
    if spec.confirm_required and not confirm:
        raise PermissionError("confirmation-required")

    cache_dir = ensure_cache_dir()
    log_path = spec.log_path(cache_dir)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    details_extra: Dict[str, Any] = {}
    if name in {"cockpit-up", "cockpit-down"}:
        steps = _render_steps(spec, payload)
        exit_code, rendered_commands = _execute_steps(steps, log_path)
    else:
        exit_code, rendered_commands, details_extra = _run_special_action(
            name,
            payload,
            confirm,
            log_path,
            job_id=job_id,
        )

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
    if details_extra:
        details.update(details_extra)
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
