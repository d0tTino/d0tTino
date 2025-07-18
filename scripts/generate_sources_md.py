#!/usr/bin/env python3
"""Generate docs/awesome-sources.md from metadata/sources.json."""

from __future__ import annotations

from typing import Iterable, cast

import json
from pathlib import Path


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
            tags_list = cast(Iterable[str], src.get("tags", []))
            tags = ", ".join(tags_list)

            license = src.get("license", "Unknown")

            details: list[str] = [f"*License:* {license}", f"*Tags:* {tags}"]
            api_type = src.get("api_type")
            if api_type:
                details.append(f"*API:* {api_type}")
            stars = src.get("stars")
            if stars:
                details.append(f"*Stars:* {stars}")

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
