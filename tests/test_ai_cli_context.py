import json
import io
import contextlib
import pytest

pytest.importorskip("requests")

from scripts import ai_cli


def test_context_switch_affects_send(monkeypatch, tmp_path):
    session_file = tmp_path / ".config" / "d0tTino" / "cli_session.json"
    monkeypatch.setattr(ai_cli, "SESSION_FILE", session_file)
    ai_cli._session.clear()

    sent_contexts = []

    def fake_send(prompt, *, local=False, model=ai_cli.router.DEFAULT_MODEL, context=None):
        sent_contexts.append(context)
        return "ok"

    monkeypatch.setattr(ai_cli.router, "send_prompt", fake_send)

    try:
        assert ai_cli.main(["switch-context", "personal"]) == 0
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            assert ai_cli.main(["send", "msg1"]) == 0
        assert out.getvalue().strip() == "ok"

        assert ai_cli.main(["switch-context", "group"]) == 0
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            assert ai_cli.main(["send", "msg2"]) == 0
        assert out.getvalue().strip() == "ok"

        assert sent_contexts == ["personal", "group"]
        data = json.loads(session_file.read_text())
        assert data["context"] == "group"
    finally:
        ai_cli._session.clear()


def test_switch_context_invalid_value():
    with pytest.raises(SystemExit) as excinfo:
        ai_cli.main(["switch-context", "invalid"])
    assert excinfo.value.code == 2
