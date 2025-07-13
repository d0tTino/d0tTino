"""Utilities for anonymous telemetry."""
from __future__ import annotations

import os
import uuid
from typing import Any

import requests


def analytics_default() -> bool:
    """Return ``True`` when ``EVENTS_ENABLED`` is set to a truthy value."""
    val = os.environ.get("EVENTS_ENABLED")
    return str(val).lower() in {"1", "true", "yes", "y"}


def record_event(name: str, payload: dict[str, Any], *, enabled: bool = False) -> None:
    """Send ``payload`` to ``EVENTS_URL`` when ``enabled`` is ``True``."""
    if not enabled:
        return
    url = os.environ.get("EVENTS_URL")
    if not url:
        return
    token = os.environ.get("EVENTS_TOKEN")
    headers = {}
    if token:
        headers["apikey"] = token
        headers["Authorization"] = f"Bearer {token}"
    dev_src = (
        os.environ.get("GIT_AUTHOR_EMAIL")
        or os.environ.get("EMAIL")
        or os.environ.get("USER")
        or "unknown"
    )
    developer = uuid.uuid5(uuid.NAMESPACE_DNS, dev_src).hex
    data = {"name": name, "developer": developer, **payload}
    try:
        requests.post(url, headers=headers, json=data, timeout=5)
    except Exception:
        pass


__all__ = ["analytics_default", "record_event"]
