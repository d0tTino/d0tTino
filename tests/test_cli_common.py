from scripts import cli_common


def test_record_event_skips_when_disabled(monkeypatch):
    monkeypatch.setenv("EVENTS_URL", "https://example.com")
    called = []

    def fake_post(url, headers=None, json=None, timeout=None):
        called.append(True)

    monkeypatch.setattr(cli_common.requests, "post", fake_post)
    cli_common.record_event("name", {"a": 1}, enabled=False)
    assert not called


def test_record_event_posts(monkeypatch):
    monkeypatch.setenv("EVENTS_URL", "https://example.com")
    monkeypatch.setenv("EVENTS_TOKEN", "tok")
    sent = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        sent["url"] = url
        sent["headers"] = headers
        sent["data"] = json

    monkeypatch.setattr(cli_common.requests, "post", fake_post)
    cli_common.record_event("name", {"a": 1}, enabled=True)

    assert sent["url"] == "https://example.com"
    assert sent["data"] == {"name": "name", "a": 1}
    assert sent["headers"]["Authorization"] == "Bearer tok"


def test_record_event_requires_url(monkeypatch):
    called = []

    def fake_post(url, headers=None, json=None, timeout=None):
        called.append(True)

    monkeypatch.setattr(cli_common.requests, "post", fake_post)
    monkeypatch.delenv("EVENTS_URL", raising=False)
    cli_common.record_event("name", {"a": 1}, enabled=True)

    assert not called
