import json
from pathlib import Path

from scripts import plugins

REPO_ROOT = Path(__file__).resolve().parents[1]
REG_PATH = REPO_ROOT / "plugin-registry.json"


def test_plugin_registry_up_to_date() -> None:
    data = json.loads(REG_PATH.read_text(encoding="utf-8"))
    plugin_pkgs = {
        name: meta.get("package") if isinstance(meta, dict) else meta
        for name, meta in data.get("plugins", {}).items()
    }
    assert plugin_pkgs == plugins.PLUGIN_REGISTRY, (
        "plugin-registry.json is outdated. "
        "Run 'python scripts/update_registry.py' and commit the result."
    )
    assert data.get("recipes") == plugins.RECIPE_REGISTRY, (
        "plugin-registry.json is outdated. "
        "Run 'python scripts/update_registry.py' and commit the result."
    )
