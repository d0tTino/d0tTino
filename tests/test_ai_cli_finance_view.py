from scripts import ai_cli


def test_finance_view_table(monkeypatch, capsys):
    options = [{"name": "OptA", "cost": 100, "summary": "Plan A"}]

    def fake_get(url, timeout=10):
        assert url == "https://fin/v1/finance/options"
        class Resp:
            def raise_for_status(self):
                return None
            def json(self):
                return options
        return Resp()

    monkeypatch.setattr(ai_cli.requests, "get", fake_get)
    rc = ai_cli.main(["finance", "view", "--url", "https://fin"])
    assert rc == 0
    out = capsys.readouterr().out.splitlines()
    assert "Name" in out[0]
    assert "Cost" in out[0]
    assert "OptA" in out[1]
    assert "100" in out[1]
    assert "Plan A" in out[1]


def test_finance_view_timeline(monkeypatch, capsys):
    options = [
        {
            "name": "OptA",
            "timeline": [{"time": "2024-07-12", "detail": "start"}],
        }
    ]

    def fake_get(url, timeout=10):
        class Resp:
            def raise_for_status(self):
                return None
            def json(self):
                return options
        return Resp()

    monkeypatch.setattr(ai_cli.requests, "get", fake_get)
    rc = ai_cli.main([
        "finance",
        "view",
        "--timeline",
        "--url",
        "https://fin",
    ])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert "OptA" in out
    assert "2024-07-12" in out
    assert "start" in out


def test_finance_view_empty(monkeypatch, capsys):
    def fake_get(url, timeout=10):
        class Resp:
            def raise_for_status(self):
                return None
            def json(self):
                return []
        return Resp()

    monkeypatch.setattr(ai_cli.requests, "get", fake_get)
    rc = ai_cli.main(["finance", "view", "--url", "https://fin"])
    assert rc == 0
    out = capsys.readouterr().out.splitlines()
    assert len(out) == 1
    assert "Name" in out[0]
