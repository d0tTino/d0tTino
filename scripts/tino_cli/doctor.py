"""Environment validation helpers for the ``tino doctor`` command."""

from __future__ import annotations

import shutil
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


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


def gather_report(*, skip_checks: bool = False) -> DoctorReport:
    """Collect the doctor report, optionally skipping expensive checks."""

    if skip_checks:
        checks = [
            DoctorCheck("docker", True, "Check skipped (dry-run)."),
            DoctorCheck("ports", True, "Check skipped (dry-run)."),
            DoctorCheck("git-hooks", True, "Check skipped (dry-run)."),
        ]
        return DoctorReport(checks)

    checks = [
        _check_docker_engine(),
        _check_required_ports(),
        _check_git_hooks(),
    ]
    return DoctorReport(checks)


__all__ = ["DoctorCheck", "DoctorReport", "gather_report"]
