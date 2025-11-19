"""Diagnostic helpers for the ``tino doctor`` command.

This module exposes both the legacy :func:`gather_report` interface that powers
``tino doctor`` as well as the richer :func:`gather_diagnostics` payload used by
other tooling.  Both entry points now derive their data from the same
check-building helpers so the summary, individual check results, and details all
remain consistent regardless of the consumer.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, TYPE_CHECKING
from urllib.parse import urlparse

from .env import iter_env_lines

if TYPE_CHECKING:
    from .state import CLIState


@dataclass(slots=True)
class DoctorCheck:
    """Result of an individual diagnostic check."""

    name: str
    ok: bool
    message: str
    details: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "name": self.name,
            "ok": self.ok,
            "message": self.message,
        }
        if self.details:
            data["details"] = self.details
        return data


@dataclass(slots=True)
class DoctorReport:
    """Aggregate report for all diagnostic checks."""

    checks: list[DoctorCheck]

    @property
    def ok(self) -> bool:
        return all(check.ok for check in self.checks)

    def summary(self) -> dict[str, object]:
        total = len(self.checks)
        passed = sum(1 for check in self.checks if check.ok)
        failed = total - passed
        return {
            "ok": passed == total,
            "total": total,
            "passed": passed,
            "failed": failed,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "summary": self.summary(),
            "checks": [check.to_dict() for check in self.checks],
        }


_REPO_ROOT = Path(__file__).resolve().parents[2]
_CHECK_HOOKS = _REPO_ROOT / "scripts" / "check-hooks.sh"
_REQUIRED_PORTS: tuple[int, ...] = (4222, 5678, 8082, 8065, 8080, 8081, 8000)
_STATUS_ERROR = "error"
_STATUS_OK = "ok"
_STATUS_WARNING = "warning"
_STATUS_SKIPPED = "skipped"


def _check_docker_engine() -> DoctorCheck:
    """Return Docker availability status."""

    docker_path = shutil.which("docker")
    details: dict[str, object] = {"path": docker_path}
    if docker_path is None:
        return DoctorCheck("docker", False, "Docker executable not found in PATH.", details)

    try:
        info_proc = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        return DoctorCheck("docker", False, "Docker executable not found in PATH.", details)
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        details["error"] = message
        return DoctorCheck("docker", False, "Docker daemon is not reachable.", details)
    else:
        server_version = info_proc.stdout.strip()
        if server_version:
            details["server_version"] = server_version

    try:
        compose_proc = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover - error path exercised via mocks
        message = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        details["compose_error"] = message
        return DoctorCheck("docker", False, "Docker Compose plugin is unavailable.", details)
    else:
        compose_output = compose_proc.stdout.strip() or compose_proc.stderr.strip()
        if compose_output:
            details["compose_version"] = compose_output.splitlines()[0]

    return DoctorCheck("docker", True, "Docker engine is available.", details)


def _check_required_ports(
    ports: Iterable[int] = _REQUIRED_PORTS,
    *,
    host: str = "127.0.0.1",
    timeout: float = 0.2,
) -> DoctorCheck:
    """Detect whether any of the published ports are already in use."""

    occupied: list[int] = []
    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            try:
                result = sock.connect_ex((host, port))
            except OSError:
                # Treat transient socket errors as the port being unavailable to avoid false positives.
                result = 0
            if result == 0:
                occupied.append(port)

    details: dict[str, object] = {
        "host": host,
        "ports": list(ports),
        "occupied": occupied,
    }
    if occupied:
        return DoctorCheck("ports", False, "One or more published ports are already in use.", details)
    return DoctorCheck("ports", True, "All required ports are available.", details)


def _check_git_hooks() -> DoctorCheck:
    """Run the Git hook validation script."""

    if not _CHECK_HOOKS.exists():
        return DoctorCheck(
            "git-hooks",
            False,
            "Hook validation script is missing.",
            {"path": str(_CHECK_HOOKS)},
        )

    proc = subprocess.run(
        ["bash", str(_CHECK_HOOKS)],
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    ok = proc.returncode == 0 and not stderr
    message = stdout or stderr or "Git hooks check executed."
    return DoctorCheck(
        "git-hooks",
        ok,
        message,
        {
            "stdout": stdout,
            "stderr": stderr,
            "returncode": proc.returncode,
        },
    )


_CHECK_BUILDERS: Mapping[str, str] = {
    "docker": "_check_docker_engine",
    "ports": "_check_required_ports",
    "git-hooks": "_check_git_hooks",
}


def _build_doctor_checks(
    *, skip_checks: bool = False, names: Iterable[str] | None = None
) -> dict[str, DoctorCheck]:
    """Return :class:`DoctorCheck` objects for the requested check names."""

    ordered_names = tuple(names) if names is not None else tuple(_CHECK_BUILDERS.keys())
    checks: dict[str, DoctorCheck] = {}
    if skip_checks:
        for name in ordered_names:
            checks[name] = DoctorCheck(name, True, "Check skipped (dry-run).")
        return checks

    for name in ordered_names:
        builder_name = _CHECK_BUILDERS.get(name)
        if builder_name is None:  # pragma: no cover - defensive guard for programming errors
            raise KeyError(f"Unknown doctor check: {name}")
        builder = globals().get(builder_name)
        if not callable(builder):  # pragma: no cover - defensive guard
            raise TypeError(f"Invalid builder configured for '{name}': {builder}")
        checks[name] = builder()
    return checks


def _payload_from_doctor_check(check: DoctorCheck) -> dict[str, Any]:
    """Translate :class:`DoctorCheck` data into a diagnostics payload."""

    payload: dict[str, Any] = {
        "status": _STATUS_OK if check.ok else _STATUS_ERROR,
        "ok": check.ok,
        "message": check.message,
    }
    if check.details:
        payload["details"] = check.details
    return payload


def gather_report(*, skip_checks: bool = False) -> DoctorReport:
    """Collect the doctor report, optionally skipping expensive checks."""

    checks = list(_build_doctor_checks(skip_checks=skip_checks).values())
    return DoctorReport(checks)


_ENV_HINTS = ("TOKEN", "API_KEY", "PASSWORD", "USERNAME", "SECRET")


@dataclass(slots=True)
class CheckSummary:
    """Aggregate status information for a diagnostic category."""

    status: str
    errors: int = 0
    warnings: int = 0


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

    shared_checks = _build_doctor_checks(
        skip_checks=state.dry_run, names=("docker", "git-hooks")
    )
    checks = {
        "docker": _payload_from_doctor_check(shared_checks["docker"]),
        "services": _service_endpoints(state.services, dry_run=state.dry_run),
        "env_tokens": _env_tokens_check(),
        "git_hooks": _payload_from_doctor_check(shared_checks["git-hooks"]),
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


__all__ = ["DoctorCheck", "DoctorReport", "gather_report", "gather_diagnostics"]
