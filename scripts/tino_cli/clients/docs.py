"""Client helpers for docs publishing automation."""
from __future__ import annotations

from pathlib import Path
from typing import Mapping

from .base import BaseClient, RequestResult
from ..config import DOCS
from ..state import CLIState


class DocsClient(BaseClient):
    """Client for documentation publishing workflows."""

    def __init__(self) -> None:
        super().__init__(name="docs", config=DOCS)

    def publish(
        self,
        state: CLIState,
        *,
        target: str,
        site: str | None = None,
        version: str | None = None,
        telemetry_extra: Mapping[str, object] | None = None,
    ) -> RequestResult | None:
        payload: dict[str, object] = {"target": target}
        path = Path(target)
        if path.exists():
            payload["path"] = str(path)
        else:
            payload["doc_id"] = target
        if site:
            payload["site"] = site
        if version:
            payload["version"] = version
        return self.request(
            state,
            "post",
            "/docs/publish",
            json_payload=payload,
            telemetry_action="publish",
            telemetry_extra=telemetry_extra,
        )


__all__ = ["DocsClient"]
