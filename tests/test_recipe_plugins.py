import importlib
import importlib.metadata
import sys
import types

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
        recipes,
        "discover_entry_points",
        lambda group: iter([entry]),
    )

    mapping = recipes.discover_recipes()
    assert mapping["dummy"]("goal") == ["dummy:goal"]

