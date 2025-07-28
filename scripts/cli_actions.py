from __future__ import annotations

import logging
import time
import asyncio
from pathlib import Path
from typing import Iterable, Callable, Sequence, Any

from ume import events as ume_events

from scripts.cli_common import execute_steps
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
    steps: Iterable[str],
    *,
    log_path: Path,
    analytics: bool = False,
    payload: dict[str, Any] | None = None,
    duration_key: str = "latency_ms",
    nats_url: str | None = None,
) -> int:
    """Execute ``steps`` and record an analytics event."""
    start = time.time()
    exit_code = execute_steps(steps, log_path=log_path)
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
) -> int:
    """Execute a recipe and record an analytics event."""
    if callable(steps_or_callable):
        steps = list(steps_or_callable(goal))
    else:
        steps = list(steps_or_callable)
    return run_steps(
        "ai-do-recipe",
        steps,
        log_path=log_path,
        analytics=analytics,
        payload={"recipe": name, "goal": goal, "step_count": len(steps)},
        nats_url=nats_url,
    )

__all__ = ["record_event_logged", "run_steps", "run_recipe"]
