from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, AsyncIterator


from nats.aio.client import Client as NATS
from nats.js import JetStreamContext

logger = logging.getLogger(__name__)

DEFAULT_NATS_URL = os.environ.get("NATS_URL", "nats://127.0.0.1:4222")
DEFAULT_SUBJECT = os.environ.get("NATS_SUBJECT", "telemetry.events")


async def _connect(url: str = DEFAULT_NATS_URL) -> NATS:
    nc = NATS()
    await nc.connect(
        servers=[url],
        connect_timeout=1,
        max_reconnect_attempts=1,
        reconnect_time_wait=1,
    )
    return nc


async def publish_event(
    name: str,
    payload: dict[str, Any],
    *,
    subject: str = DEFAULT_SUBJECT,
    url: str = DEFAULT_NATS_URL,
    nc: NATS | None = None,
) -> bool:
    """Publish ``payload`` to NATS and return ``True`` when successful."""
    data = json.dumps({"name": name, **payload}).encode("utf-8")
    close = False
    if nc is None:
        close = True
        nc = await _connect(url)
    try:
        await nc.publish(subject, data)
        await nc.flush()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to publish telemetry event: %s", exc)
        return False
    finally:
        if close:
            await nc.drain()
    return True


async def iter_events(
    *,
    subject: str = DEFAULT_SUBJECT,
    url: str = DEFAULT_NATS_URL,
    nc: NATS | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Yield events from ``subject`` as dictionaries."""
    close = False
    if nc is None:
        close = True
        nc = await _connect(url)
    sub = await nc.subscribe(subject)
    try:
        while True:
            msg = await sub.next_msg()
            yield json.loads(msg.data.decode("utf-8"))
    finally:
        await sub.unsubscribe()
        if close:
            await nc.drain()


async def publish_event_js(
    name: str,
    payload: dict[str, Any],
    *,
    subject: str = DEFAULT_SUBJECT,
    url: str = DEFAULT_NATS_URL,
    nc: NATS | None = None,
) -> bool:
    """Publish ``payload`` to JetStream and return ``True`` when successful."""
    data = json.dumps({"name": name, **payload}).encode("utf-8")
    close = False
    if nc is None:
        close = True
        nc = await _connect(url)
    js: JetStreamContext = nc.jetstream()
    try:
        await js.publish(subject, data)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to publish telemetry event to JetStream: %s", exc)
        return False
    finally:
        if close:
            await nc.drain()
    return True


async def iter_events_js(
    *,
    subject: str = DEFAULT_SUBJECT,
    url: str = DEFAULT_NATS_URL,
    nc: NATS | None = None,
    durable: str = "ume_iter",
    batch: int = 1,
) -> AsyncIterator[dict[str, Any]]:
    """Yield events from JetStream ``subject`` as dictionaries."""
    close = False
    if nc is None:
        close = True
        nc = await _connect(url)
    js: JetStreamContext = nc.jetstream()
    sub = await js.pull_subscribe(subject, durable=durable)
    try:
        while True:
            msgs = await sub.fetch(batch)
            for msg in msgs:
                yield json.loads(msg.data.decode("utf-8"))
                await msg.ack()
    finally:
        await sub.unsubscribe()
        if close:
            await nc.drain()


def publish_event_sync(name: str, payload: dict[str, Any], *, enabled: bool = False) -> bool:
    """Synchronous helper used by CLI tools."""
    if not enabled:
        return False
    try:
        return asyncio.run(publish_event(name, payload))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to publish telemetry event: %s", exc)
        return False


__all__ = [
    "publish_event",
    "publish_event_sync",
    "publish_event_js",
    "iter_events",
    "iter_events_js",
    "DEFAULT_NATS_URL",
    "DEFAULT_SUBJECT",
]

