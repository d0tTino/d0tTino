import pytest
import uuid

pytest.importorskip("requests")
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
    monkeypatch.setenv("USER", "alice")
    sent = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        sent["url"] = url
        sent["headers"] = headers
        sent["data"] = json

    monkeypatch.setattr(cli_common.requests, "post", fake_post)
    cli_common.record_event("name", {"a": 1}, enabled=True)

    assert sent["url"] == "https://example.com"
    expected_dev = uuid.uuid5(uuid.NAMESPACE_DNS, "alice").hex
    assert sent["data"] == {"name": "name", "a": 1, "developer": expected_dev}
    assert sent["headers"]["Authorization"] == "Bearer tok"


def test_record_event_requires_url(monkeypatch):
    called = []

    def fake_post(url, headers=None, json=None, timeout=None):
        called.append(True)

    monkeypatch.setattr(cli_common.requests, "post", fake_post)
    monkeypatch.delenv("EVENTS_URL", raising=False)
    cli_common.record_event("name", {"a": 1}, enabled=True)

    assert not called


def test_record_event_empty_url(monkeypatch):
    monkeypatch.setenv("EVENTS_URL", "")
    called = []

    def fake_post(url, headers=None, json=None, timeout=None):
        called.append(True)

    monkeypatch.setattr(cli_common.requests, "post", fake_post)
    cli_common.record_event("name", {"a": 1}, enabled=True)

    assert not called


def test_record_event_accepts_invalid_timestamps(monkeypatch):
    monkeypatch.setenv("EVENTS_URL", "https://example.com")
    sent = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        sent.update({"url": url, "data": json})

    monkeypatch.setattr(cli_common.requests, "post", fake_post)
    cli_common.record_event(
        "ai-do",
        {"end_ts": "not-a-number", "exit_code": 0},
        enabled=True,
    )

    assert sent["data"]["end_ts"] == "not-a-number"



def test_analytics_default(monkeypatch):
    monkeypatch.setenv("EVENTS_ENABLED", "yes")
    assert cli_common.analytics_default() is True
    monkeypatch.setenv("EVENTS_ENABLED", "0")
    assert cli_common.analytics_default() is False


def test_execute_steps_parses_quoted_args(monkeypatch, tmp_path):
    inputs = iter(["y", "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    captured = {}

    def fake_run(cmd, *, shell, capture_output, text):
        captured["cmd"] = cmd
        captured["shell"] = shell

        class Result:
            def __init__(self):
                self.stdout = ""
                self.stderr = ""
                self.returncode = 0

        return Result()

    monkeypatch.setattr(cli_common.subprocess, "run", fake_run)

    cli_common.execute_steps(["echo 'foo bar'"], log_path=tmp_path / "log.txt")

    assert captured["cmd"] == ["echo", "foo bar"]
    assert captured["shell"] is False


def test_execute_steps_fallbacks_to_shell(monkeypatch, tmp_path):
    inputs = iter(["y", "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    captured = {}

    def fake_run(cmd, *, shell, capture_output, text):
        captured["cmd"] = cmd
        captured["shell"] = shell

        class Result:
            def __init__(self):
                self.stdout = ""
                self.stderr = ""
                self.returncode = 0

        return Result()

    monkeypatch.setattr(cli_common.subprocess, "run", fake_run)

    cli_common.execute_steps(["python -c \"print('hi')\""], log_path=tmp_path / "log.txt")

    assert captured["cmd"] == "python -c \"print('hi')\""
    assert captured["shell"] is True
