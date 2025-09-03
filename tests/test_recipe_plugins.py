import importlib
import importlib.metadata
import sys
import types
from pathlib import Path
import pytest

pytest.importorskip("requests")

from scripts import recipes
from plugins.utils import discover_entry_points  # noqa: F401


def test_discover_recipes_finds_builtin_sample():
    mapping = recipes.discover_recipes()
    assert "sample" in mapping
    assert mapping["sample"]("goal") == ["echo goal"]
    assert "build" in mapping
    assert mapping["build"]("app") == ["echo build app"]
    assert "test" in mapping
    assert mapping["test"]("app") == ["echo test app"]
    assert "deploy" in mapping
    assert mapping["deploy"]("app") == ["echo deploy app"]


def test_discover_recipes_loads_entry_points(monkeypatch):
    module = types.ModuleType("dummy_recipe")
    exec(
        "def run(goal: str):\n    return ['dummy:' + goal]\n",
        module.__dict__,
    )
    sys.modules["dummy_recipe"] = module

    entry = importlib.metadata.EntryPoint(
        name="dummy",
        value="dummy_recipe:run",
        group="d0ttino.recipes",
    )

    monkeypatch.setattr(
        importlib.metadata,
        "entry_points",
        lambda *args, **kwargs: importlib.metadata.EntryPoints((entry,)),
    )

    mapping = recipes.discover_recipes()
    assert mapping["dummy"]("goal") == ["dummy:goal"]


@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires Python 3.10+")
def test_discover_recipes_loads_entry_points_py310(monkeypatch):
    module = types.ModuleType("dummy_recipe")
    exec(
        "def run(goal: str):\n    return ['dummy:' + goal]\n",
        module.__dict__,
    )
    sys.modules["dummy_recipe"] = module

    entry = importlib.metadata.EntryPoint(
        name="dummy",
        value="dummy_recipe:run",
        group="d0ttino.recipes",
    )

    def fake_entry_points(*args, **kwargs):
        if args or kwargs != {"group": recipes.RECIPE_ENTRYPOINT_GROUP}:
            raise AssertionError("entry_points called with group")
        return importlib.metadata.EntryPoints((entry,))

    monkeypatch.setattr(importlib.metadata, "entry_points", fake_entry_points)

    mapping = recipes.discover_recipes()
    assert "dummy" in mapping


def test_builtin_curated_recipes():
    mapping = recipes.discover_recipes()
    config_dir = Path(__file__).resolve().parent.parent / "scripts" / "recipes" / "config"
    assert mapping["wsl"]("") == [
        f"winget configure -f {config_dir / 'wsl.yaml'}",
        "wsl --set-default-version 2",
    ]
    assert mapping["docker_desktop"]("") == [
        f"winget configure -f {config_dir / 'docker_desktop.yaml'}",
        "wsl --set-default-version 2",
    ]
    assert mapping["vscode"]("") == [
        f"winget configure -f {config_dir / 'vscode.yaml'}",
        "code --install-extension ms-python.python",
        "code --install-extension ms-toolsai.jupyter",
    ]
    assert mapping["gpu_drivers"]("") == [
        f"winget configure -f {config_dir / 'gpu_drivers.yaml'}",
    ]
    assert mapping["powershell"]("") == [
        f"winget configure -f {config_dir / 'powershell.yaml'}",
    ]
    assert mapping["nodejs"]("") == [
        f"winget configure -f {config_dir / 'nodejs.yaml'}",
    ]
    assert mapping["git"]("") == [
        f"winget configure -f {config_dir / 'git.yaml'}",
    ]
    assert mapping["starship"]("") == [
        f"winget configure -f {config_dir / 'starship.yaml'}",
    ]
    assert mapping["windows_terminal"]("") == [
        f"winget configure -f {config_dir / 'windows_terminal.yaml'}",
    ]
    assert mapping["fastfetch"]("") == [
        f"winget configure -f {config_dir / 'fastfetch.yaml'}",
    ]

