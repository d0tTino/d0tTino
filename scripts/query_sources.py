#!/usr/bin/env python3
"""Search ``metadata/sources.json`` by name, category or tags."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Dict, Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCES_JSON = REPO_ROOT / "metadata" / "sources.json"


def load_sources(path: Path = SOURCES_JSON) -> List[Dict[str, Any]]:
    """Return the list of source dictionaries from ``path``."""
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def find_sources(
    *,
    name: str | None = None,
    category: str | None = None,
    tags: List[str] | None = None,
    path: Path = SOURCES_JSON,
) -> List[Dict[str, Any]]:
    """Return sources matching ``name``, ``category`` and/or ``tags``."""
    sources = load_sources(path)
    results: List[Dict[str, Any]] = []
    for src in sources:
        if name and name.lower() not in str(src.get("name", "")).lower():
            continue
        if category and category.lower() != str(src.get("category", "")).lower():
            continue
        if tags:
            src_tags = [t.lower() for t in src.get("tags", [])]
            if any(tag.lower() not in src_tags for tag in tags):
                continue
        results.append(src)
    return results


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", "-n", help="Filter by name substring")
    parser.add_argument("--category", "-c", help="Filter by category")
    parser.add_argument(
        "--tag",
        "-t",
        action="append",
        dest="tags",
        help="Filter by tag (repeatable)",
    )
    parser.add_argument(
        "--path",
        default=str(SOURCES_JSON),
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args(argv)
    matches = find_sources(
        name=args.name,
        category=args.category,
        tags=args.tags,
        path=Path(args.path),
    )
    for item in matches:
        print(f"{item['name']} - {item['url']}")
    return 0 if matches else 1


if __name__ == "__main__":
    raise SystemExit(main())
