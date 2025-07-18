import pytest

pytest.importorskip("requests")

from scripts import nsm_upload, nsm_stats


def test_nsm_upload_posts_counts(monkeypatch):
    events = [
        {"name": "ai-do", "exit_code": 0, "developer": "alice", "end_ts": 1693516800},
        {"name": "ai-do", "exit_code": 0, "developer": "bob", "end_ts": 1693603200},
    ]
    monkeypatch.setattr(nsm_upload.nsm_stats, "iter_events", lambda src: iter(events))

    sent = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        sent["url"] = url
        sent["headers"] = headers
        sent["json"] = json

    monkeypatch.setattr(nsm_upload.requests, "post", fake_post)
    monkeypatch.setenv("EVENTS_URL", "https://example.com")
    monkeypatch.setenv("EVENTS_TOKEN", "tok")

    rc = nsm_upload.main(["dummy.json"])
    expected = nsm_stats.aggregate_successful_runs(events)

    assert rc == 0
    assert sent["url"] == "https://example.com"
    assert sent["json"] == expected
    assert sent["headers"]["Authorization"] == "Bearer tok"


def test_nsm_upload_handles_error(monkeypatch):
    monkeypatch.setattr(nsm_upload.nsm_stats, "iter_events", lambda src: iter(()))

    def fake_post(url, headers=None, json=None, timeout=None):
        raise RuntimeError("nope")

    monkeypatch.setattr(nsm_upload.requests, "post", fake_post)
    monkeypatch.setenv("EVENTS_URL", "https://example.com")
    rc = nsm_upload.main(["dummy.json"])
    assert rc == 1
