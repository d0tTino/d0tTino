"""Client helpers for docs publishing automation."""
from __future__ import annotations

from .base import BaseClient, RequestResult
from ..config import DOCS
from ..state import CLIState


class DocsClient(BaseClient):
    """Client for documentation publishing workflows."""

    def __init__(self) -> None:
        super().__init__(name="docs", config=DOCS)

    def publish(self, state: CLIState, *, site: str, version: str | None = None) -> RequestResult | None:
        payload = {"site": site}
        if version:
            payload["version"] = version
        return self.request(state, "post", "/docs/publish", json_payload=payload, telemetry_action="publish")


__all__ = ["DocsClient"]
