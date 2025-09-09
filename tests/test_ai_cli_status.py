import contextlib
import importlib
import io
import sys

from scripts import ai_cli
import pytest


def test_status_reports_budget_depletion(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_ROUTER_BUDGET", "1")
    monkeypatch.setenv("LLM_ROUTING_MODE", "remote")
    monkeypatch.setenv("LLM_BUDGET_PATH", str(tmp_path / "budget.json"))
    sys.modules.pop("llm.router", None)
    router = importlib.import_module("llm.router")
    importlib.reload(router)
    monkeypatch.setattr(ai_cli, "router", router)
    monkeypatch.setattr(router, "_preferred_backends", lambda: ("gemini", None))
    monkeypatch.setattr(router, "run_gemini", lambda prompt, model=None: "ok")

    ai_cli.main(["send", "hi"])

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(["status"])
    assert rc == 0
    assert out.getvalue().splitlines() == [
        "Budget remaining: 0/1 (0%)",
        "Usage meter: [##########]",
        "Routing mode: remote",
        "Last model source: gemini",
    ]


def test_status_reports_partial_budget_usage(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_ROUTER_BUDGET", "2")
    monkeypatch.setenv("LLM_ROUTING_MODE", "remote")
    monkeypatch.setenv("LLM_BUDGET_PATH", str(tmp_path / "budget.json"))
    sys.modules.pop("llm.router", None)
    router = importlib.import_module("llm.router")
    importlib.reload(router)
    monkeypatch.setattr(ai_cli, "router", router)
    monkeypatch.setattr(router, "_preferred_backends", lambda: ("gemini", None))
    monkeypatch.setattr(router, "run_gemini", lambda prompt, model=None: "ok")

    ai_cli.main(["send", "hi"])

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(["status"])
    assert rc == 0
    assert out.getvalue().splitlines() == [
        "Budget remaining: 1/2 (50%)",
        "Usage meter: [#####-----]",
        "Routing mode: remote",
        "Last model source: gemini",
    ]


def test_warns_when_budget_low(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_ROUTER_BUDGET", "10")
    monkeypatch.setenv("LLM_ROUTING_MODE", "remote")
    monkeypatch.setenv("LLM_BUDGET_PATH", str(tmp_path / "budget.json"))
    sys.modules.pop("llm.router", None)
    router = importlib.import_module("llm.router")
    importlib.reload(router)
    monkeypatch.setattr(ai_cli, "router", router)
    monkeypatch.setattr(router, "_preferred_backends", lambda: ("gemini", None))
    monkeypatch.setattr(router, "run_gemini", lambda prompt, model=None: "ok")

    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        ai_cli.main(["send", "one two three four five six seven eight nine"])
    assert "budget nearly exhausted" in err.getvalue()


def test_daily_limit_warning_and_enforcement(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_ROUTER_BUDGET", "100")
    monkeypatch.setenv("LLM_ROUTING_MODE", "remote")
    monkeypatch.setenv("LLM_BUDGET_PATH", str(tmp_path / "budget.json"))
    monkeypatch.setenv("LLM_DAILY_LIMIT", "5")
    sys.modules.pop("llm.router", None)
    router = importlib.import_module("llm.router")
    importlib.reload(router)
    monkeypatch.setattr(ai_cli, "router", router)
    monkeypatch.setattr(router, "_preferred_backends", lambda: ("gemini", None))
    monkeypatch.setattr(router, "run_gemini", lambda prompt, model=None: "ok")

    ai_cli.main(["send", "one two three four"])
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        ai_cli.main(["send", "five"])
    assert "daily limit nearly exhausted" in err.getvalue()
    with pytest.raises(RuntimeError):
        ai_cli.main(["send", "six"])


def test_status_reports_daily_usage(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_ROUTER_BUDGET", "100")
    monkeypatch.setenv("LLM_ROUTING_MODE", "remote")
    monkeypatch.setenv("LLM_BUDGET_PATH", str(tmp_path / "budget.json"))
    monkeypatch.setenv("LLM_DAILY_LIMIT", "10")
    sys.modules.pop("llm.router", None)
    router = importlib.import_module("llm.router")
    importlib.reload(router)
    monkeypatch.setattr(ai_cli, "router", router)
    monkeypatch.setattr(router, "_preferred_backends", lambda: ("gemini", None))
    monkeypatch.setattr(router, "run_gemini", lambda prompt, model=None: "ok")

    ai_cli.main(["send", "one two three"])

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(["status"])
    assert rc == 0
    assert out.getvalue().splitlines() == [
        "Budget remaining: 97/100 (97%)",
        "Usage meter: [----------]",
        "Routing mode: remote",
        "Last model source: gemini",
        "Daily usage: 3/10 (30%)",
        "Daily meter: [###-------]",
    ]
