#!/usr/bin/env python3
"""Enrich metadata/sources.json with additional information."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, List

import requests

SOURCES_JSON = Path("metadata/sources.json")


def load_sources(path: Path = SOURCES_JSON) -> List[dict[str, Any]]:
    """Return the list of source dictionaries from ``path``."""
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def infer_api_type(url: str) -> str | None:
    """Guess the API type based on the URL."""
    lower = url.lower()
    if "graphql" in lower:
        return "GraphQL"
    if "api" in lower:
        return "REST"
    return None


def fetch_github_stars(url: str) -> int | None:
    """Return the GitHub star count for ``url`` if applicable."""
    match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
    if not match:
        return None
    api_url = f"https://api.github.com/repos/{match.group(1)}/{match.group(2)}"
    try:
        resp = requests.get(api_url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        stars = data.get("stargazers_count")
        if isinstance(stars, int):
            return stars
    except requests.RequestException:
        return None
    return None


def enrich_sources(sources: List[dict[str, Any]]) -> None:
    """Update ``sources`` in-place with additional details."""
    for item in sources:
        api_type = item.get("api_type") or infer_api_type(str(item.get("url", "")))
        if api_type:
            item["api_type"] = api_type
        if "stars" not in item:
            stars = fetch_github_stars(str(item.get("url", "")))
            if stars is not None:
                item["stars"] = stars


def save_sources(sources: List[dict[str, Any]], path: Path = SOURCES_JSON) -> None:
    path.write_text(json.dumps(sources, indent=2) + "\n", encoding="utf-8")


def main(argv: List[str] | None = None) -> int:
    sources = load_sources()
    enrich_sources(sources)
    save_sources(sources)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
