import importlib
import importlib.metadata
import sys
import types
import pytest

pytest.importorskip("requests")

from scripts import recipes
from plugins.utils import discover_entry_points  # noqa: F401


def test_discover_recipes_finds_builtin_sample():
    mapping = recipes.discover_recipes()
    assert "sample" in mapping
    assert mapping["sample"]("goal") == ["echo goal"]


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

