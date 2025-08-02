import json
import contextlib
import io
import pytest

pytest.importorskip("requests")

from scripts import ai_cli, cli_actions


def test_login_persists_user_and_records_event(monkeypatch, tmp_path):
    session_file = tmp_path / ".config" / "d0tTino" / "cli_session.json"
    monkeypatch.setattr(ai_cli, "SESSION_FILE", session_file)
    ai_cli._session.clear()

    recorded = []

    def fake_record(name, payload, *, enabled=False):
        recorded.append((name, payload, enabled))
        return True

    monkeypatch.setattr(cli_actions, "record_event_logged", fake_record)

    rc = ai_cli.main(["login", "u123", "--analytics"])
    assert rc == 0
    assert session_file.exists()
    data = json.loads(session_file.read_text())
    assert data == {"user_id": "u123"}
    assert ai_cli._session["user_id"] == "u123"
    assert recorded == [("ai-cli-login", {"user_id": "u123", "exit_code": 0}, True)]


def test_user_id_included_after_login(monkeypatch, tmp_path):
    session_file = tmp_path / ".config" / "d0tTino" / "cli_session.json"
    monkeypatch.setattr(ai_cli, "SESSION_FILE", session_file)
    ai_cli._session.clear()

    recorded = []

    def fake_record(name, payload, *, enabled=False):
        recorded.append((name, payload, enabled))
        return True

    monkeypatch.setattr(cli_actions, "record_event_logged", fake_record)
    monkeypatch.setattr(ai_cli.router, "send_prompt", lambda *a, **k: "ok")

    rc = ai_cli.main(["login", "user1", "--analytics"])
    assert rc == 0
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(["send", "msg", "--analytics"])
    assert rc == 0
    assert recorded[0][0] == "ai-cli-login"
    assert recorded[1] == ("ai-cli-send", {"user_id": "user1", "exit_code": 0}, True)
