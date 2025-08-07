import contextlib
import io
import json
import time

from scripts import ai_cli


def test_finance_analyze(monkeypatch):
    captured = {}

    def fake_send(prompt, *, local=False, model=ai_cli.router.DEFAULT_MODEL):
        data = json.loads(prompt)
        captured["payload"] = data
        time.sleep(0.05)
        return json.dumps({"options": ["opt1", "opt2"]})

    monkeypatch.setattr(ai_cli.router, "send_prompt", fake_send)

    events = []
    monkeypatch.setattr(ai_cli, "_publish_event", lambda a, n, p: events.append((n, p)))

    async def fake_iter_events(*args, **kwargs):
        yield {"name": "finance-analyze-progress", "options_generated": 1}
        yield {"name": "finance-analyze-progress", "options_generated": 2}

    monkeypatch.setattr(ai_cli.ume_events, "iter_events", fake_iter_events)

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(
            [
                "finance",
                "analyze",
                "--max-options",
                "2",
                "--min-budget",
                "10",
                "--max-budget",
                "20",
                "--monthly-budget",
                "300",
            ]
        )
    assert rc == 0
    assert captured["payload"] == {
        "workflow": "FinancialDecisionSupport",
        "parameters": {
            "max_options": 2,
            "min_budget": 10.0,
            "max_budget": 20.0,
            "monthly_budget": 300.0,
        },
    }
    assert out.getvalue().splitlines() == [
        "1 options generated. View them with `ai finance view`.",
        "2 options generated. View them with `ai finance view`.",
    ]
    assert events == [
        ("finance-analyze-progress", {"options_generated": 1}),
        ("finance-analyze-progress", {"options_generated": 2}),
        ("finance-analyze", {"exit_code": 0, "option_count": 2}),
    ]


def test_finance_analyze_no_budget(monkeypatch):
    captured = {}

    def fake_send(prompt, *, local=False, model=ai_cli.router.DEFAULT_MODEL):
        data = json.loads(prompt)
        captured["payload"] = data
        return json.dumps({"options": []})

    monkeypatch.setattr(ai_cli.router, "send_prompt", fake_send)
    monkeypatch.setattr(ai_cli, "_publish_event", lambda *a, **k: None)
    rc = ai_cli.main([
        "finance",
        "analyze",
        "--max-options",
        "5",
        "--no-progress",
    ])
    assert rc == 0
    assert captured["payload"] == {
        "workflow": "FinancialDecisionSupport",
        "parameters": {"max_options": 5},
    }


def test_finance_analyze_min_budget(monkeypatch):
    captured = {}

    def fake_send(prompt, *, local=False, model=ai_cli.router.DEFAULT_MODEL):
        captured["payload"] = json.loads(prompt)
        return json.dumps({"options": []})

    monkeypatch.setattr(ai_cli.router, "send_prompt", fake_send)
    monkeypatch.setattr(ai_cli, "_publish_event", lambda *a, **k: None)
    rc = ai_cli.main(
        [
            "finance",
            "analyze",
            "--max-options",
            "1",
            "--min-budget",
            "10",
            "--no-progress",
        ]
    )
    assert rc == 0
    assert captured["payload"] == {
        "workflow": "FinancialDecisionSupport",
        "parameters": {"max_options": 1, "min_budget": 10.0},
    }


def test_finance_analyze_max_budget(monkeypatch):
    captured = {}

    def fake_send(prompt, *, local=False, model=ai_cli.router.DEFAULT_MODEL):
        captured["payload"] = json.loads(prompt)
        return json.dumps({"options": []})

    monkeypatch.setattr(ai_cli.router, "send_prompt", fake_send)
    monkeypatch.setattr(ai_cli, "_publish_event", lambda *a, **k: None)
    rc = ai_cli.main(
        [
            "finance",
            "analyze",
            "--max-options",
            "1",
            "--max-budget",
            "20",
            "--no-progress",
        ]
    )
    assert rc == 0
    assert captured["payload"] == {
        "workflow": "FinancialDecisionSupport",
        "parameters": {"max_options": 1, "max_budget": 20.0},
    }


def test_finance_analyze_monthly_budget(monkeypatch):
    captured = {}

    def fake_send(prompt, *, local=False, model=ai_cli.router.DEFAULT_MODEL):
        captured["payload"] = json.loads(prompt)
        return json.dumps({"options": []})

    monkeypatch.setattr(ai_cli.router, "send_prompt", fake_send)
    monkeypatch.setattr(ai_cli, "_publish_event", lambda *a, **k: None)
    rc = ai_cli.main(
        [
            "finance",
            "analyze",
            "--max-options",
            "1",
            "--monthly-budget",
            "300",
            "--no-progress",
        ]
    )
    assert rc == 0
    assert captured["payload"] == {
        "workflow": "FinancialDecisionSupport",
        "parameters": {"max_options": 1, "monthly_budget": 300.0},
    }


def test_finance_view(monkeypatch, capsys):
    options = [{"summary": "Buy a car"}, {"summary": "Invest"}]

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
    assert out[0].startswith("Name")
    assert "Buy a car" in out[1]
    assert "Invest" in out[2]


def test_finance_view_timeline(monkeypatch, capsys):
    options = [
        {
            "summary": "Plan",
            "timeline": [{"time": "2024-07-12", "summary": "Start"}],
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
    rc = ai_cli.main(["finance", "view", "--timeline", "--url", "https://fin"])
    assert rc == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert "2024-07-12" in out[0]
