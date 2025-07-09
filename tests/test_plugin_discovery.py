import importlib
import importlib.metadata
import sys
import types
import pytest

from llm import backends


def _reset_plugins():
    backends.clear_registry()
    for mod in list(sys.modules):
        if mod.startswith("llm.backends.plugins"):  # clear plugin modules
            sys.modules.pop(mod)
    sys.modules.pop("dummy_plugin", None)

def test_discover_plugins_ignores_import_errors(monkeypatch):
    _reset_plugins()

    original_import = importlib.metadata.import_module

    def fake_import(name, package=None):
        if name == "llm.backends.plugins.guidance":
            raise ImportError("missing guidance")
        return original_import(name, package)

    monkeypatch.setattr(importlib.metadata, "import_module", fake_import)

    backends.discover_plugins()

    assert "guidance" not in backends.available_backends()


def test_discover_plugins_handles_missing_optional_dependency(monkeypatch):
    _reset_plugins()

    original_import = importlib.metadata.import_module

    def fake_import(name, package=None):
        if name == "llm.backends.plugins.gemini_dspy":
            raise ImportError("dspy missing")
        return original_import(name, package)

    monkeypatch.setattr(importlib.metadata, "import_module", fake_import)

    backends.discover_plugins()

    assert "gemini" in backends.available_backends()


def test_discover_plugins_loads_entry_points(monkeypatch):
    _reset_plugins()

    module = types.ModuleType("dummy_plugin")
    exec(
        "from llm.backends import register_backend\n"
        "def run(prompt: str, model: str | None = None) -> str:\n"
        "    return 'dummy'\n"
        "register_backend('dummy', run)\n"
        "__all__ = ['run']\n",
        module.__dict__,
    )
    sys.modules["dummy_plugin"] = module

    entry = importlib.metadata.EntryPoint(
        name="dummy",
        value="dummy_plugin",
        group="llm.plugins",
    )

    monkeypatch.setattr(
        importlib.metadata,
        "entry_points",
        lambda: importlib.metadata.EntryPoints((entry,)),
    )

    backends.discover_plugins()

    assert "dummy" in backends.available_backends()


def test_backends_import_loads_entry_point_plugins(monkeypatch):
    _reset_plugins()

    entry = importlib.metadata.EntryPoint(
        name="dummy",
        value="dummy_plugin",
        group="llm.plugins",
    )

    original_import = importlib.metadata.import_module

    def fake_import(name, package=None):
        if name == "dummy_plugin":
            module = types.ModuleType("dummy_plugin")
            exec(
                "from llm.backends import register_backend\n"
                "def run(prompt: str, model: str | None = None) -> str:\n"
                "    return 'dummy'\n"
                "register_backend('dummy', run)\n"
                "__all__ = ['run']\n",
                module.__dict__,
            )
            sys.modules["dummy_plugin"] = module
            return module
        return original_import(name, package)

    monkeypatch.setattr(
        importlib.metadata,
        "entry_points",
        lambda: importlib.metadata.EntryPoints((entry,)),
    )
    monkeypatch.setattr(importlib.metadata, "import_module", fake_import)

    reloaded = importlib.reload(backends)
    reloaded.load_backends()

    assert "dummy" in reloaded.available_backends()
    _reset_plugins()


def test_backends_import_skips_unknown_entry_points(monkeypatch):
    _reset_plugins()

    entry = importlib.metadata.EntryPoint(
        name="ghost",
        value="ghost_plugin",
        group="llm.plugins",
    )

    monkeypatch.setattr(
        importlib.metadata,
        "entry_points",
        lambda: importlib.metadata.EntryPoints((entry,)),
    )

    reloaded = importlib.reload(backends)
    reloaded.load_backends()

    assert "ghost" not in reloaded.available_backends()
    _reset_plugins()


@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires Python 3.10+")
def test_discover_plugins_loads_entry_points_py310(monkeypatch):
    _reset_plugins()

    module = types.ModuleType("dummy_plugin")
    exec(
        "from llm.backends import register_backend\n"
        "def run(prompt: str, model: str | None = None) -> str:\n"
        "    return 'dummy'\n"
        "register_backend('dummy', run)\n"
        "__all__ = ['run']\n",
        module.__dict__,
    )
    sys.modules["dummy_plugin"] = module

    entry = importlib.metadata.EntryPoint(
        name="dummy",
        value="dummy_plugin",
        group="llm.plugins",
    )

    def fake_entry_points(*args, **kwargs):
        if args or kwargs:
            raise AssertionError("entry_points called with arguments")
        return importlib.metadata.EntryPoints((entry,))

    monkeypatch.setattr(importlib.metadata, "entry_points", fake_entry_points)

    backends.discover_plugins()

    assert "dummy" in backends.available_backends()
