import pytest

from llm.backends import OpenRouterBackend
from llm import router as ai_router


def test_openrouter_backend_returns_string():
    backend = OpenRouterBackend("m")
    assert backend.run("p") == "openrouter:p:m"


def test_run_openrouter_uses_dspy_backend(monkeypatch):
    dspy = pytest.importorskip("dspy")  # noqa: F841 - ensure dependency present

    calls = []

    class Dummy:
        def __init__(self, model):
            calls.append(("init", model))

        def run(self, prompt: str) -> str:
            calls.append(("run", prompt))
            return "dspy"

    class Fail:
        def __init__(self, *a, **k):
            raise AssertionError("OpenRouterBackend should not be used")

    monkeypatch.setattr(ai_router, "OpenRouterDSPyBackend", Dummy)
    monkeypatch.setattr(ai_router, "OpenRouterBackend", Fail)

    out = ai_router.run_openrouter("hi", "model")
    assert out == "dspy"
    assert calls == [("init", "model"), ("run", "hi")]


def test_run_openrouter_without_dspy(monkeypatch):
    calls = []

    class Dummy:
        def __init__(self, model):
            calls.append(("init", model))

        def run(self, prompt: str) -> str:
            calls.append(("run", prompt))
            return "cli"

    monkeypatch.setattr(ai_router, "OpenRouterDSPyBackend", None)
    monkeypatch.setattr(ai_router, "OpenRouterBackend", Dummy)

    out = ai_router.run_openrouter("yo", "m")
    assert out == "cli"
    assert calls == [("init", "m"), ("run", "yo")]
