"""Client helpers for Unified Memory Engine (UME) automation."""
from __future__ import annotations

from typing import Any, Mapping

from .base import BaseClient, RequestResult
from ..config import UME
from ..state import CLIState


class UMEClient(BaseClient):
    """Client for UME idea capture and memory querying."""

    def __init__(self) -> None:
        super().__init__(name="ume", config=UME)

    def submit_idea(self, state: CLIState, *, text: str) -> RequestResult | None:
        payload = {"idea": text}
        return self.request(state, "post", "/ideas", json_payload=payload, telemetry_action="idea")

    def query(self, state: CLIState, *, query: str, filters: Mapping[str, Any] | None = None) -> RequestResult | None:
        payload: dict[str, object] = {"query": query}
        if filters:
            payload["filters"] = filters
        return self.request(state, "post", "/memories/query", json_payload=payload, telemetry_action="query")


__all__ = ["UMEClient"]
