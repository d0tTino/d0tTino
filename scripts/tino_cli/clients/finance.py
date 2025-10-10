"""Client helpers for finance micro-services."""
from __future__ import annotations

from typing import Mapping

from .base import BaseClient, RequestResult
from ..config import FINANCE
from ..state import CLIState


class FinanceClient(BaseClient):
    """Simple client for finance automation helpers."""

    def __init__(self) -> None:
        super().__init__(name="finance", config=FINANCE)

    def summarize(
        self, state: CLIState, *, period: str, month: str | None = None
    ) -> RequestResult | None:
        return self.snapshot(state, period=period, month=month)

    def snapshot(
        self, state: CLIState, *, period: str, month: str | None = None
    ) -> RequestResult | None:
        payload = {"period": period}
        if month:
            payload["month"] = month
        return self.request(state, "post", "/finance/report", json_payload=payload, telemetry_action="report")

    def sync(self, state: CLIState, *, provider: str) -> RequestResult | None:
        payload = {"provider": provider}
        return self.request(state, "post", "/finance/sync", json_payload=payload, telemetry_action="sync")


__all__ = ["FinanceClient"]
