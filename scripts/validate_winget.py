#!/usr/bin/env python3
"""Validate ``winget-packages.json`` contains sources with packages."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def validate(path: Path) -> bool:
    """Return ``True`` when ``path`` is a valid packages file."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to parse {path}: {exc}", file=sys.stderr)
        return False

    sources = data.get("Sources")
    if not isinstance(sources, list) or not sources:
        print(f"{path} has no sources", file=sys.stderr)
        return False

    for idx, source in enumerate(sources):
        if not isinstance(source, dict):
            print(f"{path} source index {idx} is not an object", file=sys.stderr)
            return False
        packages = source.get("Packages")
        if not isinstance(packages, list) or not packages:
            name = source.get("Name", f"index {idx}")
            print(f"{path} source {name} has no packages", file=sys.stderr)
            return False

    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default="winget-packages.json")
    args = parser.parse_args(argv)
    return 0 if validate(Path(args.path)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
