from scripts import ai_cli, cli_actions


def test_calendar_add(monkeypatch):
    recorded = []

    def fake_record(name, payload, *, enabled=False):
        recorded.append((name, payload, enabled))
        return True

    monkeypatch.setattr(cli_actions, "record_event_logged", fake_record)

    captured = {}

    class FakeAgent:
        def add_event(self, text):
            captured["text"] = text

    monkeypatch.setattr(ai_cli, "_load_calendar_agent", lambda: FakeAgent)

    rc = ai_cli.main(["calendar", "add", "Lunch tomorrow", "--analytics"])
    assert rc == 0
    assert captured["text"] == "Lunch tomorrow"
    name, payload, enabled = recorded[0]
    assert name == "ai-cli-calendar-add"
    assert payload["exit_code"] == 0
    assert enabled is True


def test_calendar_add_missing_agent(monkeypatch, capsys):
    recorded = []

    def fake_record(name, payload, *, enabled=False):
        recorded.append((name, payload, enabled))
        return True

    monkeypatch.setattr(cli_actions, "record_event_logged", fake_record)
    monkeypatch.setattr(ai_cli, "_load_calendar_agent", lambda: None)

    rc = ai_cli.main(["calendar", "add", "Lunch", "--analytics"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "CalendarNLP_Agent is not available" in err
    name, payload, enabled = recorded[0]
    assert name == "ai-cli-calendar-add"
    assert payload["exit_code"] == 1
    assert enabled is True


def test_calendar_view(monkeypatch, capsys):
    events = [
        {
            "start": "2024-07-12T10:00:00",
            "end": "2024-07-12T11:00:00",
            "summary": "Meeting",
            "layer": "work",
        }
    ]

    def fake_get(url, params=None, timeout=10):
        assert url == "https://cal/v1/calendar/events"
        assert params["day"] == "2024-07-12"
        assert params["layers"] == "work"

        class Resp:
            def raise_for_status(self):
                return None

            def json(self):
                return events

        return Resp()

    monkeypatch.setattr(ai_cli.requests, "get", fake_get)
    rc = ai_cli.main(
        ["calendar", "view", "--day", "2024-07-12", "--layers", "work", "--url", "https://cal"]
    )
    assert rc == 0
    out = capsys.readouterr().out.splitlines()
    assert "Start" in out[0]
    assert "Meeting" in out[1]


def test_calendar_view_timeline(monkeypatch, capsys):
    events = [
        {
            "start": "2024-07-12T10:00:00",
            "end": "2024-07-12T11:00:00",
            "summary": "Meeting",
        }
    ]

    def fake_get(url, params=None, timeout=10):
        assert params["week"] == "2024-W28"

        class Resp:
            def raise_for_status(self):
                return None

            def json(self):
                return events

        return Resp()

    monkeypatch.setattr(ai_cli.requests, "get", fake_get)
    rc = ai_cli.main(
        [
            "calendar",
            "view",
            "--week",
            "2024-W28",
            "--timeline",
            "--url",
            "https://cal",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert "Meeting" in out
    assert "2024-07-12T10:00:00" in out
