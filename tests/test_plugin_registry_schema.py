import json
from pathlib import Path

import jsonschema
from jsonschema import FormatChecker

REPO_ROOT = Path(__file__).resolve().parents[1]

SCHEMA_PATH = REPO_ROOT / "plugin-registry.schema.json"
REGISTRY_PATH = REPO_ROOT / "plugin-registry.json"


def test_plugin_registry_schema_valid() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(data, schema, format_checker=FormatChecker())


def test_registry_documents_commands_and_templates() -> None:
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    commands = {cmd["name"]: cmd for cmd in data["commands"]}
    assert "aiga:deploy" in commands
    assert commands["aiga:deploy"]["exec"].startswith("python -m")

    templates = {tpl["id"]: tpl for tpl in data["taskTemplates"]}
    assert "weekly-review" in templates
    template = templates["weekly-review"]
    assert template["metadata"]["cadence"] == "weekly"
