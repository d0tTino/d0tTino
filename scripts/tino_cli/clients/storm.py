"""Client helpers for the tino-storm research stack."""
from __future__ import annotations

from typing import Mapping

from .base import BaseClient, RequestResult
from ..config import STORM
from ..state import CLIState


class StormClient(BaseClient):
    """Client for the tino-storm research ingestion and drafting APIs."""

    def __init__(self) -> None:
        super().__init__(name="storm", config=STORM)

    def ingest(self, state: CLIState, *, topic: str, source: str) -> RequestResult | None:
        payload = {"topic": topic, "source": source}
        return self.request(state, "post", "/research/ingest", json_payload=payload, telemetry_action="ingest")

    def draft(self, state: CLIState, *, topic: str, hints: Mapping[str, str] | None = None) -> RequestResult | None:
        payload: dict[str, object] = {"topic": topic}
        if hints:
            payload["hints"] = hints
        return self.request(state, "post", "/research/draft", json_payload=payload, telemetry_action="draft")


__all__ = ["StormClient"]
