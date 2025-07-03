import pytest

pytest.importorskip("requests")  # ensure dependency present

from llm.backends.superclaude import SuperClaudeBackend
from llm import router as ai_router


def test_superclaude_backend_returns_string(monkeypatch):
    def fake_post(url, json, timeout):
        class Resp:
            def raise_for_status(self):
                pass

            def json(self):
                return {"text": f"{json['prompt']}-{json['model']}"}

        return Resp()

    monkeypatch.setattr("requests.post", fake_post)
    backend = SuperClaudeBackend("m")
    result = backend.run("p")
    assert result == "p-m"


def test_run_superclaude_invokes_backend(monkeypatch):
    calls = []

    class Dummy:
        def __init__(self, model):
            calls.append(("init", model))

        def run(self, prompt: str) -> str:
            calls.append(("run", prompt))
            return "sc"

    monkeypatch.setattr(ai_router, "SuperClaudeBackend", Dummy)

    out = ai_router.run_superclaude("hi", "model")
    assert out == "sc"
    assert calls == [("init", "model"), ("run", "hi")]
