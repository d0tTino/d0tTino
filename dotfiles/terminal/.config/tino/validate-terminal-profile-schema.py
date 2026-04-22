#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import jsonschema


def _schema_path() -> Path:
    return Path(__file__).with_name("terminal-profile.schema.json")


def _coerce_float(field: str, value: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be a number, got {value!r}") from exc


def _coerce_int(field: str, value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be an integer, got {value!r}") from exc


def build_profile(provider: str) -> dict[str, object]:
    env = os.environ
    return {
        "provider": provider,
        "opacity": _coerce_float("opacity", env.get("TINO_TERMINAL_OPACITY", "")),
        "fps": _coerce_int("fps", env.get("TINO_TERMINAL_FPS", "")),
        "effects": env.get("TINO_TERMINAL_EFFECTS", ""),
        "palette": {
            "background": env.get("TINO_TERMINAL_BACKGROUND", ""),
            "foreground": env.get("TINO_TERMINAL_FOREGROUND", ""),
            "cursor": env.get("TINO_TERMINAL_CURSOR", ""),
            "selection": env.get("TINO_TERMINAL_SELECTION", ""),
            **{f"color_{i}": env.get(f"TINO_TERMINAL_COLOR_{i}", "") for i in range(16)},
        },
    }


def _format_field(error: jsonschema.ValidationError) -> str:
    if not error.path:
        return "<root>"
    return ".".join(str(part) for part in error.path)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"Usage: {Path(argv[0]).name} <provider>", file=sys.stderr)
        return 1

    provider = argv[1]
    schema_path = _schema_path()
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Error: failed to load terminal profile schema at {schema_path}: {exc}", file=sys.stderr)
        return 1

    try:
        profile = build_profile(provider)
    except ValueError as exc:
        print(f"Error: terminal profile schema pre-validation failed: {exc}", file=sys.stderr)
        return 1

    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(profile), key=lambda err: list(err.path))
    if not errors:
        return 0

    print("Error: terminal profile schema validation failed.", file=sys.stderr)
    for error in errors:
        field = _format_field(error)
        print(f"- field '{field}': {error.message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
