#!/usr/bin/env python3
"""Generate docs/awesome-sources.md from metadata/sources.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, cast


SOURCES_JSON = Path("metadata/sources.json")
OUTPUT_MD = Path("docs/awesome-sources.md")


def load_sources(path: Path = SOURCES_JSON) -> list[dict[str, object]]:
    """Return the list of source dictionaries from ``path``."""
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def generate_markdown(sources: list[dict[str, object]]) -> str:
    """Return Markdown content for ``sources``."""
    lines: list[str] = ["# Awesome Sources", "", "A curated list of useful resources.", ""]
    categories: dict[str, list[dict[str, object]]] = {}
    for item in sources:
        category = str(item["category"])

        categories.setdefault(category, []).append(item)
    for category in sorted(categories):
        lines.append(f"## {category}")
        for src in categories[category]:
            raw_tags = src.get("tags", [])
            tags_list = list(raw_tags) if isinstance(raw_tags, list) else []
            tags = ", ".join(str(t) for t in tags_list)
            license = src.get("license", "Unknown")

            lines.append(
                f"- [{src['name']}]({src['url']}) — " + " — ".join(details)
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    sources = load_sources()
    markdown = generate_markdown(sources)
    OUTPUT_MD.write_text(markdown, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
