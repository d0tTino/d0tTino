from __future__ import annotations

import asyncio
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ume.events as events


class FakeNATS:
    def __init__(self):
        self.published = []
        self.connected = []
        self.drained = False

    async def connect(self, servers=None):
        self.connected.append(servers)

    async def publish(self, subject, data):
        self.published.append((subject, data))

    async def flush(self):
        pass

    async def drain(self):
        self.drained = True

    async def subscribe(self, subject):
        self.subscribed = subject
        return FakeSub()


class FakeSub:
    def __init__(self):
        self.messages = [FakeMsg(b"{\"a\": 1}")]

    async def next_msg(self):
        if self.messages:
            return self.messages.pop(0)
        raise asyncio.CancelledError

    async def unsubscribe(self):
        self.unsub = True


class FakeMsg:
    def __init__(self, data):
        self.data = data


def test_publish_event_sync(monkeypatch):
    fake = FakeNATS()

    async def fake_connect(url=events.DEFAULT_NATS_URL):
        fake.url = url
        return fake

    monkeypatch.setattr(events, "_connect", fake_connect)
    success = events.publish_event_sync("test", {"x": 2}, enabled=True)
    assert success is True
    assert fake.published == [
        (events.DEFAULT_SUBJECT, b'{"name": "test", "x": 2}')
    ]
    assert fake.drained is True


@pytest.mark.asyncio
async def test_iter_events(monkeypatch):
    fake = FakeNATS()

    async def fake_connect(url=events.DEFAULT_NATS_URL):
        return fake

    monkeypatch.setattr(events, "_connect", fake_connect)
    gen = events.iter_events()
    event = await gen.__anext__()
    assert event == {"a": 1}
    await gen.aclose()
