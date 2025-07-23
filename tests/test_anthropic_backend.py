import pytest

pytest.importorskip("requests")

from llm import router as ai_router
from llm.backends.plugins import anthropic as plugin


def test_run_anthropic(monkeypatch):
    calls = []

    class Dummy:
        def __init__(self, model):
            calls.append(("init", model))

        def run(self, prompt: str) -> str:
            calls.append(("run", prompt))
            return "anthro"

    monkeypatch.setattr(plugin, "AnthropicBackend", Dummy)

    out = ai_router.run_anthropic("hey", "m")
    assert out == "anthro"
    assert calls == [("init", "m"), ("run", "hey")]
