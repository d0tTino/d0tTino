"""Diagnostic helpers for the ``tino doctor`` command."""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
from dataclasses import dataclass
from typing import Any, Mapping, Sequence, TYPE_CHECKING
from urllib.parse import urlparse

from .env import _REPO_ROOT, iter_env_lines

if TYPE_CHECKING:
    from .state import CLIState


_STATUS_ERROR = "error"
_STATUS_OK = "ok"
_STATUS_WARNING = "warning"
_STATUS_SKIPPED = "skipped"

_ENV_HINTS = ("TOKEN", "API_KEY", "PASSWORD", "USERNAME", "SECRET")


@dataclass(slots=True)
class CheckSummary:
    """Aggregate status information for a diagnostic category."""

    status: str
    errors: int = 0
    warnings: int = 0


def _docker_check() -> dict[str, Any]:
    """Return Docker availability information."""

    executable = shutil.which("docker")
    if not executable:
        return {
            "status": _STATUS_ERROR,
            "available": False,
            "message": "Docker CLI not found on PATH.",
        }

    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError as exc:  # pragma: no cover - exercised in environments without docker
        return {
            "status": _STATUS_ERROR,
            "available": False,
            "message": f"Failed to execute docker: {exc}",
        }

    output = (result.stdout or result.stderr or "").strip()
    status = _STATUS_OK if result.returncode == 0 else _STATUS_ERROR
    message = output or None
    return {
        "status": status,
        "available": True,
        "message": message,
        "return_code": result.returncode,
    }


def _service_endpoints(services: Mapping[str, str], *, dry_run: bool) -> dict[str, Any]:
    """Report reachability of configured service endpoints."""

    items: list[dict[str, Any]] = []
    reachable_count = 0
    skipped = dry_run

    for name, url in services.items():
        parsed = urlparse(url)
        host = parsed.hostname or "127.0.0.1"
        if parsed.scheme == "unix":
            # Docker sockets are reported as unix:// paths; treat as reachable.
            items.append(
                {
                    "name": name,
                    "url": url,
                    "host": host,
                    "port": None,
                    "reachable": True,
                    "status": _STATUS_OK,
                    "note": "Unix socket endpoint",
                }
            )
            reachable_count += 1
            continue

        port = parsed.port
        if port is None:
            if parsed.scheme == "https":
                port = 443
            else:
                port = 80

        item_status = _STATUS_SKIPPED if dry_run else _STATUS_WARNING
        error: str | None = None
        reachable = None if dry_run else False
        if not dry_run:
            try:
                with socket.create_connection((host, port), timeout=1):
                    reachable = True
                    item_status = _STATUS_OK
                    reachable_count += 1
            except OSError as exc:
                error = str(exc)
        items.append(
            {
                "name": name,
                "url": url,
                "host": host,
                "port": port,
                "reachable": reachable,
                "status": item_status,
                "error": error,
            }
        )

    if skipped:
        status = _STATUS_SKIPPED
    elif reachable_count == len(items) and items:
        status = _STATUS_OK
    elif reachable_count > 0:
        status = _STATUS_WARNING
    else:
        status = _STATUS_WARNING if items else _STATUS_OK

    return {
        "status": status,
        "items": items,
        "reachable": reachable_count,
        "total": len(items),
        "dry_run": dry_run,
    }


def _collect_env_keys() -> Sequence[str]:
    """Return credential-like environment keys derived from repository defaults."""

    keys: set[str] = set()
    for path in (_REPO_ROOT / ".env", _REPO_ROOT / ".env.example"):
        for key, _ in iter_env_lines(path):
            if any(hint in key for hint in _ENV_HINTS):
                keys.add(key)
    return tuple(sorted(keys))


def _env_tokens_check() -> dict[str, Any]:
    """Report presence of authentication tokens in the environment."""

    keys = _collect_env_keys()
    items: list[dict[str, Any]] = []
    missing: list[str] = []
    for key in keys:
        value = os.environ.get(key)
        present = bool(value)
        if not present:
            missing.append(key)
        items.append({"name": key, "present": present})

    if not keys:
        status = _STATUS_SKIPPED
    elif missing:
        status = _STATUS_WARNING
    else:
        status = _STATUS_OK

    return {
        "status": status,
        "items": items,
        "missing": missing,
        "checked": list(keys),
    }


def _git_hooks_check() -> dict[str, Any]:
    """Return git hook configuration status."""

    try:
        result = subprocess.run(
            ["git", "config", "--get", "core.hooksPath"],
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError as exc:  # pragma: no cover - git unavailable in execution environment
        return {
            "status": _STATUS_ERROR,
            "hooks_path": None,
            "message": f"Failed to query git configuration: {exc}",
        }

    hooks_path = result.stdout.strip()
    if hooks_path:
        message = f"Git hooks path is set to '{hooks_path}'"
        status = _STATUS_OK
    else:
        message = "Git hooks are not configured. Run ./scripts/setup-hooks.sh to enable them."
        status = _STATUS_WARNING

    return {
        "status": status,
        "hooks_path": hooks_path or None,
        "message": message,
    }


def _summarise(checks: Mapping[str, Mapping[str, Any]]) -> CheckSummary:
    """Aggregate overall severity from individual checks."""

    errors = 0
    warnings = 0
    for payload in checks.values():
        status = payload.get("status")
        if status == _STATUS_ERROR:
            errors += 1
        elif status == _STATUS_WARNING:
            warnings += 1
    if errors:
        overall = _STATUS_ERROR
    elif warnings:
        overall = _STATUS_WARNING
    else:
        overall = _STATUS_OK
    return CheckSummary(status=overall, errors=errors, warnings=warnings)


def gather_diagnostics(state: CLIState) -> dict[str, Any]:
    """Return a structured diagnostics report for the CLI environment."""

    checks = {
        "docker": _docker_check(),
        "services": _service_endpoints(state.services, dry_run=state.dry_run),
        "env_tokens": _env_tokens_check(),
        "git_hooks": _git_hooks_check(),
    }
    summary = _summarise(checks)
    return {
        "dry_run": state.dry_run,
        "confirm": state.confirm,
        "summary": {
            "status": summary.status,
            "errors": summary.errors,
            "warnings": summary.warnings,
        },
        "checks": checks,
    }


__all__ = ["gather_diagnostics"]
