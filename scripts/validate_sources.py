#!/usr/bin/env python3
"""Validate ``metadata/sources.json`` against its JSON schema."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import jsonschema
from jsonschema import FormatChecker

SCHEMA_PATH = Path("metadata/sources.schema.json")
SOURCES_JSON = Path("metadata/sources.json")


def validate(path: Path = SOURCES_JSON, schema_path: Path = SCHEMA_PATH) -> bool:
    """Return ``True`` if ``path`` conforms to the schema."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"{path} not found", file=sys.stderr)
        return False
    except json.JSONDecodeError as exc:
        print(f"Failed to parse {path}: {exc}", file=sys.stderr)
        return False

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - schema load failure
        print(f"Failed to load schema {schema_path}: {exc}", file=sys.stderr)
        return False

    try:
        jsonschema.validate(data, schema, format_checker=FormatChecker())
    except jsonschema.ValidationError as exc:
        print(f"{path} failed validation: {exc.message}", file=sys.stderr)
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=str(SOURCES_JSON))
    parser.add_argument("--schema", default=str(SCHEMA_PATH))
    args = parser.parse_args(argv)
    return 0 if validate(Path(args.path), Path(args.schema)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
