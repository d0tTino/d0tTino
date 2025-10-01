"""HTTP and WebSocket client helpers for :mod:`scripts.tino_cli`."""
from __future__ import annotations

import json
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator, Mapping, MutableMapping
from urllib.parse import urljoin

import requests
import typer

from telemetry import record_event

from ..config import ServiceConfig
from ..state import CLIState

DEFAULT_TIMEOUT = 10


@dataclass(slots=True)
class RequestResult:
    """Container for rich information about a performed HTTP request."""

    status: int
    url: str
    duration_ms: float
    payload: Any


class BaseClient:
    """Base class that implements HTTP helpers with telemetry integration."""

    def __init__(self, *, name: str, config: ServiceConfig):
        self.name = name
        self.config = config
        self.session = requests.Session()

    def _build_url(self, path: str | None = None) -> str:
        base = self.config.resolve()
        if not path:
            return base
        return urljoin(f"{base.rstrip('/')}/", path.lstrip("/"))

    def _record(
        self,
        *,
        state: CLIState,
        action: str,
        url: str,
        duration_ms: float | None = None,
        status: int | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> None:
        if not state.telemetry_enabled:
            return
        payload: dict[str, Any] = {
            "action": action,
            "url": url,
            "status": status,
        }
        if duration_ms is not None:
            payload["duration_ms"] = duration_ms
        if extra:
            payload.update(extra)
        record_event(
            f"tino_cli.{self.name}.{action}",
            payload,
            enabled=True,
        )

    def request(
        self,
        state: CLIState,
        method: str,
        path: str,
        *,
        json_payload: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        allow_redirects: bool = True,
        telemetry_action: str | None = None,
    ) -> RequestResult | None:
        """Perform an HTTP request or print a dry-run preview."""

        url = self._build_url(path)
        action = telemetry_action or method.lower()
        if state.dry_run:
            typer.echo(f"[dry-run] {method.upper()} {url}")
            if json_payload:
                typer.echo(json.dumps(json_payload, indent=2))
            self._record(state=state, action=action, url=url, extra={"dry_run": True})
            return None
        start = time.perf_counter()
        response = self.session.request(
            method,
            url,
            json=json_payload,
            params=params,
            timeout=timeout,
            allow_redirects=allow_redirects,
        )
        duration_ms = (time.perf_counter() - start) * 1000
        payload: Any
        try:
            payload = response.json()
        except ValueError:
            payload = response.text
        self._record(
            state=state,
            action=action,
            url=url,
            duration_ms=duration_ms,
            status=response.status_code,
        )
        response.raise_for_status()
        return RequestResult(
            status=response.status_code,
            url=url,
            duration_ms=duration_ms,
            payload=payload,
        )

    def stream(
        self,
        state: CLIState,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        telemetry_action: str = "stream",
        timeout: int = DEFAULT_TIMEOUT,
    ) -> Iterator[str]:
        """Yield log lines by streaming a request to ``path``."""

        url = self._build_url(path)
        if state.dry_run:
            typer.echo(f"[dry-run] stream {url}")
            self._record(state=state, action=telemetry_action, url=url, extra={"dry_run": True})
            return iter(())
        start = time.perf_counter()
        with self.session.get(url, params=params, stream=True, timeout=timeout) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                text = line.decode("utf-8", errors="replace")
                yield text
        duration_ms = (time.perf_counter() - start) * 1000
        self._record(
            state=state,
            action=telemetry_action,
            url=url,
            duration_ms=duration_ms,
            status=200,
        )

    @contextmanager
    def websocket(
        self,
        state: CLIState,
        path: str,
        *,
        headers: MutableMapping[str, str] | None = None,
    ) -> Iterator[None]:
        """Context manager placeholder for WebSocket connections."""

        url = self._build_url(path)
        if state.dry_run:
            typer.echo(f"[dry-run] websocket {url}")
            self._record(state=state, action="websocket", url=url, extra={"dry_run": True})
            yield None
            return
        try:
            import websockets  # type: ignore
        except Exception as exc:  # noqa: BLE001
            typer.echo(
                "WebSocket support requires the 'websockets' extra dependency.",
                err=True,
            )
            self._record(
                state=state,
                action="websocket",
                url=url,
                extra={"error": str(exc)},
            )
            raise typer.Exit(2) from exc
        async def _connect() -> None:
            async with websockets.connect(url, extra_headers=headers):
                return None
        # The CLI primarily relies on streaming HTTP. Provide a no-op placeholder
        # so plug-ins can hook into WebSocket-capable implementations when the
        # optional dependency is installed.
        yield from ()


__all__ = ["BaseClient", "RequestResult"]
