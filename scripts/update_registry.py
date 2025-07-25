#!/usr/bin/env python3
"""Validate and update plugin-registry.json from built-in defaults."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import jsonschema
from jsonschema import FormatChecker

from scripts import plugins

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "plugin-registry.json"
SCHEMA_PATH = REPO_ROOT / "plugin-registry.schema.json"


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, object]:
    """Return registry data from ``path``."""
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def load_schema(path: Path = SCHEMA_PATH) -> dict[str, object]:
    """Return JSON schema from ``path``."""
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def validate_registry(data: dict[str, object], schema: dict[str, object]) -> None:
    """Raise ``jsonschema.ValidationError`` if ``data`` is invalid."""
    jsonschema.validate(data, schema, format_checker=FormatChecker())


def sync_registry(data: dict[str, object]) -> bool:
    """Update ``data`` with built-in registry values.

    Returns ``True`` if ``data`` was modified.
    """
    expected_plugins = plugins.PLUGIN_REGISTRY
    expected_recipes = plugins.RECIPE_REGISTRY
    changed = False
    if data.get("plugins") != expected_plugins:
        data["plugins"] = expected_plugins
        changed = True
    if data.get("recipes") != expected_recipes:
        data["recipes"] = expected_recipes
        changed = True
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Return non-zero if plugin-registry.json is outdated",
    )
    args = parser.parse_args(argv)

    try:
        data = load_registry()
    except json.JSONDecodeError as exc:
        print(f"Failed to parse {REGISTRY_PATH}: {exc}", file=sys.stderr)
        return 1

    schema = load_schema()
    try:
        validate_registry(data, schema)
    except jsonschema.ValidationError as exc:
        print(f"{REGISTRY_PATH} failed validation: {exc.message}", file=sys.stderr)
        return 1

    changed = sync_registry(data)
    if changed:
        if args.check:
            print(
                "plugin-registry.json is outdated. "
                "Run 'python scripts/update_registry.py' and commit the result.",
                file=sys.stderr,
            )
            return 1
        REGISTRY_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
