"""Shared dataclasses and helpers for CLI responses."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence


@dataclass(slots=True)
class TelemetryStatus:
    """Describe telemetry configuration for the command execution."""

    enabled: bool
    endpoint: str | None = None


@dataclass(slots=True)
class CommandResult:
    """Standard payload returned by most commands."""

    message: str
    telemetry: TelemetryStatus | None = None
    details: Dict[str, Any] | None = None


@dataclass(slots=True)
class DashboardSummary:
    """Information rendered on the cockpit dashboard."""

    recent_plans: List[str]
    budget: int | None
    budget_history: List[int]
    plugins: List[Dict[str, Any]]


@dataclass(slots=True)
class ActionSpec:
    """Descriptor for cockpit actions handled by the CLI."""

    name: str
    steps: Sequence[str]
    description: str
    confirm_required: bool = False
    log_name: str | None = None

    def log_path(self, root: Path) -> Path:
        """Return the path where execution logs should be stored."""

        filename = self.log_name or f"{self.name}.log"
        return root / filename


__all__ = [
    "ActionSpec",
    "CommandResult",
    "DashboardSummary",
    "TelemetryStatus",
]
