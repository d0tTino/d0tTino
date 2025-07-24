import pytest

from llm import backends
from llm.backends import plugin_sdk


@pytest.fixture(autouse=True)
def restore_registry():
    backends_snapshot = dict(backends._BACKEND_REGISTRY)
    recipes_snapshot = dict(plugin_sdk._RECIPE_REGISTRY)
    try:
        yield
    finally:
        backends._BACKEND_REGISTRY.clear()
        backends._BACKEND_REGISTRY.update(backends_snapshot)
        plugin_sdk._RECIPE_REGISTRY.clear()
        plugin_sdk._RECIPE_REGISTRY.update(recipes_snapshot)


def test_register_backend_adds_callable():
    def run(prompt: str, model: str | None = None) -> str:
        return f"dummy:{prompt}:{model}"

    plugin_sdk.register_backend("Dummy", run)

    assert "dummy" in backends.available_backends()
    assert backends.get_backend("dummy") is run


def test_register_and_get_registered_recipes():
    def recipe(goal: str) -> list[str]:
        return [f"echo {goal}"]

    plugin_sdk.register_recipe("echo", recipe)

    recipes = plugin_sdk.get_registered_recipes()
    assert recipes["echo"] is recipe

    recipes["echo"] = lambda _: ["nope"]
    assert plugin_sdk.get_registered_recipes()["echo"] is recipe
