from __future__ import annotations

import json
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib

from scripts.helpers.generate_palette_artifacts import ANSI_ORDER
from scripts.helpers.starship_spec import (
    REQUIRED_MODULE_KEYS,
    REQUIRED_MODULE_VALUES,
    STARSHIP_PROMPT_FORMAT,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
STARSHIP_PATH = REPO_ROOT / "dotfiles" / "shell" / ".config" / "starship.toml"
PALETTES_PATH = REPO_ROOT / "metadata" / "palettes.json"


def load_starship() -> dict[str, object]:
    return tomllib.loads(STARSHIP_PATH.read_text(encoding="utf-8"))


def expected_default_palette() -> tuple[str, dict[str, str]]:
    config = json.loads(PALETTES_PATH.read_text(encoding="utf-8"))
    default_name = config["default_palette"]
    colors = {
        key: config["palettes"][default_name]["ansi"][key]
        for key in ANSI_ORDER
    }
    return default_name, colors


__all__ = [
    "REQUIRED_MODULE_KEYS",
    "REQUIRED_MODULE_VALUES",
    "STARSHIP_PROMPT_FORMAT",
    "expected_default_palette",
    "load_starship",
]
