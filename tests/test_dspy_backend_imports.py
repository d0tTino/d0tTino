import importlib
import pytest

dspy = pytest.importorskip("dspy")  # noqa: F401 - ensure dspy is installed


@pytest.mark.parametrize("module_name, attr", [
    ("llm.backends.plugins.gemini_dspy", "GeminiDSPyBackend"),
    ("llm.backends.plugins.ollama_dspy", "OllamaDSPyBackend"),
    ("llm.backends.plugins.openrouter_dspy", "OpenRouterDSPyBackend"),
])
def test_dspy_backend_imports(module_name, attr):
    module = importlib.import_module(module_name)
    assert hasattr(module, attr)
    backend = getattr(module, attr)
    assert backend is not None
