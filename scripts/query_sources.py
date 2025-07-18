#!/usr/bin/env python3
"""Search ``metadata/sources.json`` by name or tag."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Dict, Any

SOURCES_JSON = Path("metadata/sources.json")


def load_sources(path: Path = SOURCES_JSON) -> List[Dict[str, Any]]:
    """Return the list of source dictionaries from ``path``."""
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def find_sources(
    *, name: str | None = None,
    tag: str | None = None,
    path: Path = SOURCES_JSON,
) -> List[Dict[str, Any]]:
    """Return sources matching ``name`` and/or ``tag``."""
    sources = load_sources(path)
    results: List[Dict[str, Any]] = []
    for src in sources:
        if name and name.lower() not in str(src.get("name", "")).lower():
            continue
        if tag and tag.lower() not in [t.lower() for t in src.get("tags", [])]:
            continue
        results.append(src)
    return results


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", "-n", help="Filter by name substring")
    parser.add_argument("--tag", "-t", help="Filter by tag")
    parser.add_argument(
        "--path",
        default=str(SOURCES_JSON),
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args(argv)
    matches = find_sources(name=args.name, tag=args.tag, path=Path(args.path))
    for item in matches:
        print(f"{item['name']} - {item['url']}")
    return 0 if matches else 1


if __name__ == "__main__":
    raise SystemExit(main())
