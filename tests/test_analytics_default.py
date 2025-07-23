import io
import contextlib
import pytest

pytest.importorskip("requests")

from scripts import ai_cli, cli_actions


def test_main_respects_events_enabled(monkeypatch):
    monkeypatch.setenv("EVENTS_ENABLED", "1")
    monkeypatch.setattr(ai_cli.router, "send_prompt", lambda *a, **k: "ok")

    recorded = []

    def fake_record(name, payload, *, enabled=False):
        recorded.append(enabled)
        return True

    monkeypatch.setattr(cli_actions, "record_event_logged", fake_record)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(["send", "msg"])

    assert rc == 0
    assert recorded == [True]


def test_main_skips_events_without_env(monkeypatch):
    monkeypatch.delenv("EVENTS_ENABLED", raising=False)
    monkeypatch.setattr(ai_cli.router, "send_prompt", lambda *a, **k: "ok")

    recorded = []

    def fake_record(name, payload, *, enabled=False):
        recorded.append(enabled)
        return True

    monkeypatch.setattr(cli_actions, "record_event_logged", fake_record)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(["send", "msg"])

    assert rc == 0
    assert recorded == [False]
