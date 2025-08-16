"""Helper routines for executing CLI recipes with analytics support."""
from __future__ import annotations

import logging
import time
import asyncio
import sys
from pathlib import Path
from typing import Iterable, Callable, Sequence, Any

from ume import events as ume_events

from scripts.cli_common import PlanStep, execute_steps
from telemetry import record_event
from ume.events import publish_event_sync


def record_event_logged(name: str, payload: dict[str, Any], *, enabled: bool = False) -> None:
    """Record an analytics event and log failures."""
    success = record_event(name, payload, enabled=enabled)
    if not success:
        logging.debug("Failed to record telemetry")
    publish_event_sync(name, payload, enabled=enabled)


def run_steps(
    event_name: str,
    steps: Iterable[PlanStep],
    *,
    log_path: Path,
    analytics: bool = False,
    payload: dict[str, Any] | None = None,
    duration_key: str = "latency_ms",
    nats_url: str | None = None,
    jetstream: bool = False,
    dry_run: bool = False,
    assume_yes: bool = False,
    confirm: bool = False,
    allowed_capabilities: set[str] | None = None,
) -> int:
    """Execute ``steps`` and record an analytics event."""
    start = time.time()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    step_list = [s if isinstance(s, PlanStep) else PlanStep(i + 1, s) for i, s in enumerate(steps)]
    risk_present = any("[risk:" in s.command for s in step_list)
    if assume_yes and not confirm and risk_present:
        print("Risky commands present. User confirmation required.", file=sys.stderr)
        return 1

    exit_code = execute_steps(
        step_list,
        log_path=log_path,
        dry_run=dry_run,
        assume_yes=assume_yes,
        confirm=confirm,
        allowed_capabilities=allowed_capabilities,
    )
    end = time.time()
    data = {
        "exit_code": exit_code,
        "start_ts": start,
        "end_ts": end,
        duration_key: int((end - start) * 1000),
    }
    if payload:
        data.update(payload)
    record_event_logged(event_name, data, enabled=analytics)
    if analytics and nats_url:
        try:
            if jetstream:
                asyncio.run(ume_events.publish_event_js(nats_url, event_name, data))  # type: ignore[misc,arg-type]
            else:
                asyncio.run(ume_events.publish_event(nats_url, event_name, data))  # type: ignore[misc,arg-type]

        except Exception as exc:  # noqa: BLE001
            logging.debug("Failed to publish NATS event: %s", exc)
    return exit_code


def run_recipe(
    name: str,
    goal: str,
    steps_or_callable: Sequence[str] | Callable[[str], Sequence[str]],
    *,
    log_path: Path,
    analytics: bool = False,
    nats_url: str | None = None,
    jetstream: bool = False,
    dry_run: bool = False,
    assume_yes: bool = False,
    confirm: bool = False,
    allowed_capabilities: set[str] | None = None,
) -> int:
    """Execute a recipe and record an analytics event."""
    if callable(steps_or_callable):
        raw_steps = list(steps_or_callable(goal))
    else:
        raw_steps = list(steps_or_callable)
    steps = [PlanStep(i + 1, s) for i, s in enumerate(raw_steps)]
    return run_steps(
        "ai-do-recipe",
        steps,
        log_path=log_path,
        analytics=analytics,
        payload={"recipe": name, "goal": goal, "step_count": len(steps)},
        nats_url=nats_url,
        jetstream=jetstream,
        dry_run=dry_run,
        assume_yes=assume_yes,
        confirm=confirm,
        allowed_capabilities=allowed_capabilities,
    )

__all__ = ["record_event_logged", "run_steps", "run_recipe"]
