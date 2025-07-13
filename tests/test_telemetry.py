from __future__ import annotations

import uuid

import telemetry


def test_record_event_skips_when_disabled(monkeypatch):
    monkeypatch.setenv("EVENTS_URL", "https://example.com")
    called = []

    def fake_post(url, headers=None, json=None, timeout=None):
        called.append(True)

    monkeypatch.setattr(telemetry.requests, "post", fake_post)
    telemetry.record_event("name", {"a": 1}, enabled=False)
    assert not called


def test_record_event_posts(monkeypatch):
    monkeypatch.setenv("EVENTS_URL", "https://example.com")
    monkeypatch.setenv("EVENTS_TOKEN", "tok")
    monkeypatch.setenv("USER", "alice")
    sent = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        sent["url"] = url
        sent["headers"] = headers
        sent["data"] = json

    monkeypatch.setattr(telemetry.requests, "post", fake_post)
    telemetry.record_event("name", {"a": 1}, enabled=True)

    assert sent["url"] == "https://example.com"
    expected_dev = uuid.uuid5(uuid.NAMESPACE_DNS, "alice").hex
    assert sent["data"] == {"name": "name", "a": 1, "developer": expected_dev}
    assert sent["headers"]["Authorization"] == "Bearer tok"


def test_record_event_requires_url(monkeypatch):
    called = []

    def fake_post(url, headers=None, json=None, timeout=None):
        called.append(True)

    monkeypatch.setattr(telemetry.requests, "post", fake_post)
    monkeypatch.delenv("EVENTS_URL", raising=False)
    telemetry.record_event("name", {"a": 1}, enabled=True)

    assert not called


def test_record_event_empty_url(monkeypatch):
    monkeypatch.setenv("EVENTS_URL", "")
    called = []

    def fake_post(url, headers=None, json=None, timeout=None):
        called.append(True)

    monkeypatch.setattr(telemetry.requests, "post", fake_post)
    telemetry.record_event("name", {"a": 1}, enabled=True)

    assert not called


def test_record_event_accepts_invalid_timestamps(monkeypatch):
    monkeypatch.setenv("EVENTS_URL", "https://example.com")
    sent = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        sent.update({"url": url, "data": json})

    monkeypatch.setattr(telemetry.requests, "post", fake_post)
    telemetry.record_event(
        "ai-do",
        {"end_ts": "not-a-number", "exit_code": 0},
        enabled=True,
    )

    assert sent["data"]["end_ts"] == "not-a-number"


def test_analytics_default(monkeypatch):
    monkeypatch.setenv("EVENTS_ENABLED", "yes")
    assert telemetry.analytics_default() is True
    monkeypatch.setenv("EVENTS_ENABLED", "0")
    assert telemetry.analytics_default() is False
