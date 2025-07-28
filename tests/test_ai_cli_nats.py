from __future__ import annotations

from pathlib import Path
import sys

from scripts import ai_cli

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ume.events as events


class FakeNATS:
    def __init__(self):
        self.published = []

    async def connect(self, servers=None):
        pass

    async def publish(self, subject, data):
        self.published.append((subject, data))

    async def flush(self):
        pass

    async def drain(self):
        pass


def test_ai_cli_publishes_event(monkeypatch):
    monkeypatch.setattr(ai_cli.router, "send_prompt", lambda *a, **k: "ok")

    fake = FakeNATS()

    async def fake_connect(url=events.DEFAULT_NATS_URL):
        return fake

    monkeypatch.setattr(events, "_connect", fake_connect)
    rc = ai_cli.main(["send", "msg", "--analytics"])
    assert rc == 0
    subject, data = fake.published[0]
    assert subject == events.DEFAULT_SUBJECT
    assert b"ai-cli-send" in data
