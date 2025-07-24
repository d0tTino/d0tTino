import json
from pathlib import Path

from scripts import plugins

REPO_ROOT = Path(__file__).resolve().parents[1]
REG_PATH = REPO_ROOT / "plugin-registry.json"


def test_plugin_registry_up_to_date() -> None:
    data = json.loads(REG_PATH.read_text(encoding="utf-8"))
    assert data.get("plugins") == plugins.PLUGIN_REGISTRY, (
        "plugin-registry.json is outdated. "
        "Run 'python scripts/update_registry.py' and commit the result."
    )
