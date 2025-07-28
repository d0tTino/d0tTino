from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from nats.aio.client import Client as NATS

logger = logging.getLogger(__name__)

async def _publish(url: str, subject: str, payload: dict[str, Any]) -> bool:
    nc = NATS()
    try:
        await nc.connect(servers=[url])
        await nc.publish(subject, json.dumps(payload).encode())
        await nc.flush()
        await nc.drain()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to publish to NATS: %s", exc)
        return False


def publish_event(url: str, name: str, payload: dict[str, Any]) -> bool:
    """Publish ``payload`` to ``url`` on the ``name`` subject."""
    return asyncio.run(_publish(url, name, payload))

__all__ = ["publish_event"]
