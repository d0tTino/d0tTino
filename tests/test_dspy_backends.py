import importlib
import sys
import types

import pytest


@pytest.mark.parametrize(
    "module_name, attr, model, expected",
    [
        ("llm.backends.plugins.gemini_dspy", "GeminiDSPyBackend", None, "google/gemini-pro"),
        ("llm.backends.plugins.ollama_dspy", "OllamaDSPyBackend", "m", "m"),
        ("llm.backends.plugins.openrouter_dspy", "OpenRouterDSPyBackend", "m", "m"),
    ],
)
def test_dspy_backend_can_run(monkeypatch, module_name, attr, model, expected):
    """Each DSPy backend should instantiate and return text using a dummy dspy module."""

    class DummyLM:
        def __init__(self, model=None):
            self.model = model

        def forward(self, prompt: str, **_: str):
            return {"choices": [{"message": {"content": f"{prompt}-{self.model}"}}]}

    dummy = types.SimpleNamespace(LM=DummyLM, LLM=DummyLM)
    monkeypatch.setitem(sys.modules, "dspy", dummy)
    monkeypatch.setitem(sys.modules, "requests", types.ModuleType("requests"))

    module = importlib.import_module(module_name)
    module = importlib.reload(module)

    backend_cls = getattr(module, attr)
    assert backend_cls is not None
    backend = backend_cls(model)
    result = backend.run("p")
    assert result == f"p-{expected}"
