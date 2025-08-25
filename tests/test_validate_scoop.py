import json
import urllib.request
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_validate_scoop_manifest() -> None:
    manifest_path = REPO_ROOT / "scoop" / "tino-bucket" / "tino.json"
    with manifest_path.open(encoding="utf-8") as fh:
        manifest = json.load(fh)

    with urllib.request.urlopen(
        "https://raw.githubusercontent.com/ScoopInstaller/Scoop/master/schema.json"
    ) as resp:
        schema = json.load(resp)

    jsonschema.validate(manifest, schema)
