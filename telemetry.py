"""Utilities for anonymous telemetry."""
from __future__ import annotations

import os
import uuid
from typing import Any
import logging

import requests
import aiohttp


logger = logging.getLogger(__name__)


def analytics_default() -> bool:
    """Return ``True`` when ``EVENTS_ENABLED`` is set to a truthy value."""
    val = os.environ.get("EVENTS_ENABLED")
    return str(val).lower() in {"1", "true", "yes", "y"}


def record_event(name: str, payload: dict[str, Any], *, enabled: bool = False) -> bool:
    """Send ``payload`` to ``EVENTS_URL`` when ``enabled`` is ``True``.

    Return ``True`` when the event is successfully posted.
    """
    if not enabled:
        return False
    url = os.environ.get("EVENTS_URL")
    if not url:
        return False
    token = os.environ.get("EVENTS_TOKEN")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["apikey"] = token
        headers["Authorization"] = f"Bearer {token}"
    headers.setdefault("Prefer", "return=minimal")
    dev_src = (
        os.environ.get("GIT_AUTHOR_EMAIL")
        or os.environ.get("EMAIL")
        or os.environ.get("USER")
        or "unknown"
    )
    developer = uuid.uuid5(uuid.NAMESPACE_DNS, dev_src).hex
    data = {"payload": {"name": name, "developer": developer, **payload}}
    try:
        response = requests.post(url, headers=headers, json=data, timeout=5)
        success = response.status_code // 100 == 2
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to record telemetry event: %s", exc)
        success = False

    latency = payload.get("latency_ms") or payload.get("duration_ms")
    source = payload.get("model_source", "unknown")
    logger.info("%s: source=%s latency_ms=%s", name, source, latency)
    return success


async def async_record_event(
    name: str, payload: dict[str, Any], *, enabled: bool = False, session: aiohttp.ClientSession | None = None
) -> bool:
    """Asynchronously send ``payload`` to ``EVENTS_URL`` when ``enabled`` is ``True``.

    Return ``True`` when the event is successfully posted.
    """
    if not enabled:
        return False
    url = os.environ.get("EVENTS_URL")
    if not url:
        return False
    token = os.environ.get("EVENTS_TOKEN")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["apikey"] = token
        headers["Authorization"] = f"Bearer {token}"
    headers.setdefault("Prefer", "return=minimal")
    dev_src = (
        os.environ.get("GIT_AUTHOR_EMAIL")
        or os.environ.get("EMAIL")
        or os.environ.get("USER")
        or "unknown"
    )
    developer = uuid.uuid5(uuid.NAMESPACE_DNS, dev_src).hex
    data = {"payload": {"name": name, "developer": developer, **payload}}
    close_session = False
    if session is None:
        session = aiohttp.ClientSession()
        close_session = True
    try:
        async with session.post(url, headers=headers, json=data, timeout=5) as resp:
            success = resp.status // 100 == 2
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to record telemetry event: %s", exc)
        success = False
    finally:
        if close_session:
            await session.close()

    latency = payload.get("latency_ms") or payload.get("duration_ms")
    source = payload.get("model_source", "unknown")
    logger.info("%s: source=%s latency_ms=%s", name, source, latency)
    return success


__all__ = ["analytics_default", "record_event", "async_record_event"]
