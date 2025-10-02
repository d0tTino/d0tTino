"""Client for TaskCascadence automation services."""
from __future__ import annotations

from typing import Any, Mapping

from .base import BaseClient, RequestResult
from ..config import TASKCASCADENCE
from ..state import CLIState


class TaskCascadenceClient(BaseClient):
    """Typed convenience wrapper around the TaskCascadence API."""

    def __init__(self) -> None:
        super().__init__(name="taskcascadence", config=TASKCASCADENCE)

    def run(self, state: CLIState, task: str, *, payload: Mapping[str, Any] | None = None) -> RequestResult | None:
        body = {"task": task}
        if payload:
            body["payload"] = payload
        return self.request(state, "post", "/tasks/run", json_payload=body, telemetry_action="run")

    def status(self, state: CLIState, task_id: str) -> RequestResult | None:
        return self.request(state, "get", f"/tasks/{task_id}", telemetry_action="status")

    def signal(
        self,
        state: CLIState,
        task_id: str,
        *,
        signal: str,
        link: str | None = None,
        note: str | None = None,
    ) -> RequestResult | None:
        body: dict[str, object] = {"signal": signal}
        if link:
            body["link"] = link
        if note:
            body["note"] = note
        return self.request(
            state,
            "post",
            f"/tasks/{task_id}/signal",
            json_payload=body,
            telemetry_action="signal",
        )


__all__ = ["TaskCascadenceClient"]
