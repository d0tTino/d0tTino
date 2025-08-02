import contextlib
import io
import json

from scripts import ai_cli


def test_finance_analyze(monkeypatch):
    captured = {}

    def fake_send(prompt, *, local=False, model=ai_cli.router.DEFAULT_MODEL):
        data = json.loads(prompt)
        captured["payload"] = data
        return json.dumps({"options": ["opt1", "opt2"]})

    monkeypatch.setattr(ai_cli.router, "send_prompt", fake_send)

    events = []
    monkeypatch.setattr(ai_cli, "_publish_event", lambda a, n, p: events.append((n, p)))

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
            ]
        )
    assert rc == 0
    assert captured["payload"] == {
        "workflow": "FinancialDecisionSupport",
        "parameters": {"max_options": 2, "min_budget": 10.0, "max_budget": 20.0},
    }
    assert out.getvalue().splitlines() == ["opt1", "opt2"]
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

    rc = ai_cli.main(["finance", "analyze", "--max-options", "5"])
    assert rc == 0
    assert captured["payload"] == {
        "workflow": "FinancialDecisionSupport",
        "parameters": {"max_options": 5},
    }
