import pytest

pytest.importorskip("requests")

from llm.backends import OpenRouterBackend
from llm import router as ai_router


def test_openrouter_backend_makes_request(monkeypatch):
    calls = {}

    def fake_post(url, json, headers, timeout):
        calls["url"] = url
        calls["json"] = json
        calls["headers"] = headers

        class Resp:
            def raise_for_status(self):
                pass

            def json(self):
                return {"choices": [{"message": {"content": "result"}}]}

        return Resp()

    monkeypatch.setattr("requests.post", fake_post)
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://example.com/api")

    backend = OpenRouterBackend("m")
    result = backend.run("p")

    assert result == "result"
    assert calls["url"] == "https://example.com/api/chat/completions"
    assert calls["json"] == {
        "model": "m",
        "messages": [{"role": "user", "content": "p"}],
    }
    assert calls["headers"] == {"Authorization": "Bearer k"}


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

    from llm.backends.plugins import openrouter as plugin

    monkeypatch.setattr(plugin, "OpenRouterDSPyBackend", Dummy)
    monkeypatch.setattr(plugin, "OpenRouterBackend", Fail)

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

    from llm.backends.plugins import openrouter as plugin

    monkeypatch.setattr(plugin, "OpenRouterDSPyBackend", None)
    monkeypatch.setattr(plugin, "OpenRouterBackend", Dummy)

    out = ai_router.run_openrouter("yo", "m")
    assert out == "cli"
    assert calls == [("init", "m"), ("run", "yo")]
