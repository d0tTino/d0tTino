from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCES_JSON = REPO_ROOT / "metadata" / "sources.json"


def load_sources(path: Path = SOURCES_JSON) -> list[dict[str, Any]]:
    """Return the list of source dictionaries from ``path``."""
    with path.open(encoding="utf-8") as f:
        return json.load(f)

__all__ = ["load_sources", "SOURCES_JSON"]
