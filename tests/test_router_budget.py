import importlib
import sys

import pytest


@pytest.fixture(autouse=True)
def reset_router(monkeypatch):
    yield
    monkeypatch.delenv("LLM_ROUTER_BUDGET", raising=False)
    sys.modules.pop("llm.router", None)
    importlib.import_module("llm.router")


def _reload_router(monkeypatch, budget: str = "1"):
    monkeypatch.setenv("LLM_ROUTER_BUDGET", budget)
    monkeypatch.setenv("LLM_ROUTING_MODE", "remote")
    sys.modules.pop("llm.router", None)
    return importlib.import_module("llm.router")


def test_budget_decrements_and_exhausts(monkeypatch):
    router = _reload_router(monkeypatch, "1")
    monkeypatch.setattr(router, "_preferred_backends", lambda: ("gemini", None))
    monkeypatch.setattr(router, "run_gemini", lambda prompt, model=None: "ok")

    assert router.get_budget() == 1
    router.send_prompt("hello", model="g1")
    assert router.get_budget() == 0
    with pytest.raises(RuntimeError):
        router.send_prompt("again", model="g1")


def test_local_does_not_use_budget(monkeypatch):
    router = _reload_router(monkeypatch, "1")
    monkeypatch.setattr(router, "_preferred_backends", lambda: ("gemini", "ollama"))
    monkeypatch.setattr(router, "run_ollama", lambda prompt, model: "local")

    router.send_prompt("hi", local=True, model="o1")
    assert router.get_budget() == 1
