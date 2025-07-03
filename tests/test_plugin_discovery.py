import importlib
import sys

from llm import backends


def _reset_plugins():
    backends.clear_registry()
    for mod in list(sys.modules):
        if mod.startswith("llm.backends.plugins"):  # clear plugin modules
            sys.modules.pop(mod)

def test_discover_plugins_ignores_import_errors(monkeypatch):
    _reset_plugins()

    original_import = importlib.import_module

    def fake_import(name, package=None):
        if name == "llm.backends.plugins.guidance":
            raise ImportError("missing guidance")
        return original_import(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import)

    backends.discover_plugins()

    assert "guidance" not in backends.available_backends()


def test_discover_plugins_handles_missing_optional_dependency(monkeypatch):
    _reset_plugins()

    original_import = importlib.import_module

    def fake_import(name, package=None):
        if name == "llm.backends.plugins.gemini_dspy":
            raise ImportError("dspy missing")
        return original_import(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import)

    backends.discover_plugins()

    assert "gemini" in backends.available_backends()
