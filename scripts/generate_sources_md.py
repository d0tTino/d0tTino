#!/usr/bin/env python3
"""Generate docs/awesome-sources.md from metadata/sources.json."""

from __future__ import annotations

import json
from pathlib import Path

SOURCES_JSON = Path("metadata/sources.json")
OUTPUT_MD = Path("docs/awesome-sources.md")


def load_sources(path: Path = SOURCES_JSON) -> list[dict[str, str]]:
    """Return the list of source dictionaries from ``path``."""
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def generate_markdown(sources: list[dict[str, str]]) -> str:
    """Return Markdown content for ``sources``."""
    lines: list[str] = ["# Awesome Sources", "", "A curated list of useful resources.", ""]
    categories: dict[str, list[dict[str, str]]] = {}
    for item in sources:
        categories.setdefault(item["category"], []).append(item)
    for category in sorted(categories):
        lines.append(f"## {category}")
        for src in categories[category]:
            lines.append(f"- [{src['name']}]({src['url']})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    sources = load_sources()
    markdown = generate_markdown(sources)
    OUTPUT_MD.write_text(markdown, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
