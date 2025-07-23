import importlib
import sys
from pathlib import Path
import subprocess

import pytest

pytest.importorskip("requests")
pytest.importorskip("lmql")

from llm import backends

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGINS = {
    "d0ttino-anthropic-plugin": REPO_ROOT / "examples" / "plugins" / "anthropic",
    "d0ttino-mistral-plugin": REPO_ROOT / "examples" / "plugins" / "mistral",
    "d0ttino-lmql-plugin": REPO_ROOT / "examples" / "plugins" / "lmql",
}


def _reset_plugins() -> None:
    backends.clear_registry()
    for mod in list(sys.modules):
        if mod.startswith("llm.backends.plugins"):
            sys.modules.pop(mod)


@pytest.fixture(scope="module")
def install_example_plugins():
    for path in PLUGINS.values():
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", str(path)], check=True)
    try:
        yield
    finally:
        for name in PLUGINS:
            subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", name], check=True)
        _reset_plugins()


def test_load_backends_registers_plugins(install_example_plugins):
    _reset_plugins()
    importlib.reload(backends)
    backends.load_backends()
    names = backends.available_backends()
    assert "anthropic" in names
    assert "mistral" in names
    assert "lmql" in names
