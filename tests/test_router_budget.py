import contextlib
import importlib
import io
import json
import sys
from datetime import date

import pytest

from scripts import ai_cli


@pytest.fixture(autouse=True)
def reset_router(monkeypatch):
    yield
    monkeypatch.delenv("LLM_ROUTER_BUDGET", raising=False)
    monkeypatch.delenv("LLM_BUDGET_PATH", raising=False)
    monkeypatch.delenv("LLM_DAILY_LIMIT", raising=False)
    sys.modules.pop("llm.router", None)
    router = importlib.import_module("llm.router")
    importlib.reload(router)
    monkeypatch.setattr(ai_cli, "router", router, raising=False)


def _reload_router(monkeypatch, tmp_path, budget: str = "1", daily_limit: str | None = None):
    monkeypatch.setenv("LLM_ROUTER_BUDGET", budget)
    monkeypatch.setenv("LLM_ROUTING_MODE", "remote")
    monkeypatch.setenv("LLM_BUDGET_PATH", str(tmp_path / "budget.json"))
    if daily_limit is not None:
        monkeypatch.setenv("LLM_DAILY_LIMIT", daily_limit)
    sys.modules.pop("llm.router", None)
    router = importlib.import_module("llm.router")
    importlib.reload(router)
    return router


def test_budget_decrements_and_exhausts(monkeypatch, tmp_path):
    router = _reload_router(monkeypatch, tmp_path, "2")
    monkeypatch.setattr(router, "_preferred_backends", lambda: ("gemini", None))
    monkeypatch.setattr(router, "run_gemini", lambda prompt, model=None: "ok")

    assert router.get_budget() == (2, 2, None)
    router.send_prompt("hello world", model="g1")
    assert router.get_budget() == (0, 2, "gemini")
    with pytest.raises(RuntimeError):
        router.send_prompt("again", model="g1")


def test_local_does_not_use_budget(monkeypatch, tmp_path):
    router = _reload_router(monkeypatch, tmp_path, "2")
    monkeypatch.setattr(router, "_preferred_backends", lambda: ("gemini", "ollama"))
    monkeypatch.setattr(router, "run_ollama", lambda prompt, model: "local")

    router.send_prompt("hi there", local=True, model="o1")
    assert router.get_budget() == (2, 2, "ollama")


def test_status_reports_budget_and_source(monkeypatch, tmp_path):
    router = _reload_router(monkeypatch, tmp_path, "5")
    monkeypatch.setattr(router, "_preferred_backends", lambda: ("gemini", None))
    monkeypatch.setattr(router, "run_gemini", lambda prompt, model=None: "ok")
    monkeypatch.setattr(ai_cli, "router", router)

    router.send_prompt("hello world", model="g1")

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(["status"])
    assert rc == 0
    assert out.getvalue().splitlines() == [
        "Budget remaining: 3/5 (60%)",
        "Usage meter: [####------]",
        "Routing mode: remote",
        "Last model source: gemini",
    ]


def test_budget_persists_across_sessions(monkeypatch, tmp_path):
    router = _reload_router(monkeypatch, tmp_path, "5")
    monkeypatch.setattr(router, "_preferred_backends", lambda: ("gemini", None))
    monkeypatch.setattr(router, "run_gemini", lambda prompt, model=None: "ok")
    router.send_prompt("hello world", model="g1")
    assert router.get_budget() == (3, 5, "gemini")

    sys.modules.pop("llm.router", None)
    router2 = importlib.import_module("llm.router")
    importlib.reload(router2)
    assert router2.get_budget() == (3, 5, None)


def test_daily_limit_enforced_and_persisted(monkeypatch, tmp_path):
    router = _reload_router(monkeypatch, tmp_path, "100", daily_limit="5")
    monkeypatch.setattr(router, "_preferred_backends", lambda: ("gemini", None))
    monkeypatch.setattr(router, "run_gemini", lambda prompt, model=None: "ok")
    router.send_prompt("one two", model="g1")
    router.send_prompt("three four", model="g1")
    with (tmp_path / "budget.json").open() as fh:
        data = json.load(fh)
    today = date.today().isoformat()
    assert data["daily"] == {"date": today, "used": 4}
    router = _reload_router(monkeypatch, tmp_path, "100", daily_limit="5")
    monkeypatch.setattr(router, "_preferred_backends", lambda: ("gemini", None))
    monkeypatch.setattr(router, "run_gemini", lambda prompt, model=None: "ok")
    with pytest.raises(RuntimeError):
        router.send_prompt("five six", model="g1")


def test_daily_usage_resets_next_day(monkeypatch, tmp_path):
    router = _reload_router(monkeypatch, tmp_path, "100", daily_limit="5")
    monkeypatch.setattr(router, "_preferred_backends", lambda: ("gemini", None))
    monkeypatch.setattr(router, "run_gemini", lambda prompt, model=None: "ok")
    router.send_prompt("hello world", model="g1")
    budget_file = tmp_path / "budget.json"
    with budget_file.open() as fh:
        data = json.load(fh)
    data["daily"]["date"] = "2000-01-01"
    with budget_file.open("w") as fh:
        json.dump(data, fh)
    router = _reload_router(monkeypatch, tmp_path, "100", daily_limit="5")
    monkeypatch.setattr(router, "_preferred_backends", lambda: ("gemini", None))
    monkeypatch.setattr(router, "run_gemini", lambda prompt, model=None: "ok")
    router.send_prompt("one two three four five", model="g1")
    with budget_file.open() as fh:
        data = json.load(fh)
    today = date.today().isoformat()
    assert data["daily"] == {"date": today, "used": 5}

