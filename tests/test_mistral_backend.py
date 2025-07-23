import pytest

pytest.importorskip("requests")

from llm import router as ai_router
from llm.backends.plugins import mistral as plugin


def test_run_mistral(monkeypatch):
    calls = []

    class Dummy:
        def __init__(self, model):
            calls.append(("init", model))

        def run(self, prompt: str) -> str:
            calls.append(("run", prompt))
            return "mist"

    monkeypatch.setattr(plugin, "MistralBackend", Dummy)

    out = ai_router.run_mistral("hi", "m")
    assert out == "mist"
    assert calls == [("init", "m"), ("run", "hi")]
