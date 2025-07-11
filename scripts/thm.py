#!/usr/bin/env python3
"""Terminal Harmony Manager: sync palettes across tools."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib


REPO_ROOT = Path(os.environ.get("THM_REPO_ROOT", Path(__file__).resolve().parent.parent))
PALETTES_DIR = REPO_ROOT / "palettes"


def load_palette(palette_path: Path) -> dict[str, dict[str, str]]:
    """Load and return the palette dict from ``palette_path``."""
    with palette_path.open("rb") as f:
        return tomllib.load(f)


def apply_palette(palette_name: str, repo_root: Path) -> None:
    """Apply ``palette_name`` to Starship and Windows Terminal."""
    try:
        import tomli_w
    except ModuleNotFoundError:
        print(
            "tomli_w is required; install with 'pip install -e .[cli]'",
            file=sys.stderr,
        )
        raise SystemExit(1)

    palette_file = repo_root / "palettes" / f"{palette_name}.toml"
    if not palette_file.exists():
        raise FileNotFoundError(f"Palette '{palette_name}' not found")

    palettes = load_palette(palette_file)
    if palette_name not in palettes:
        raise ValueError(
            f"Palette file '{palette_file}' does not contain key '{palette_name}'"
        )
    colors = palettes[palette_name]

    # Update starship.toml
    starship = repo_root / "starship.toml"
    if not starship.exists():
        print(f"Error: {starship} not found", file=sys.stderr)
        raise SystemExit(1)
    data = tomllib.loads(starship.read_text(encoding="utf-8"))
    data["palette"] = palette_name
    palettes = data.setdefault("palettes", {})
    palettes[palette_name] = colors
    starship.write_text(tomli_w.dumps(data) + "\n", encoding="utf-8")

    # Update Windows Terminal settings
    wt_settings = repo_root / "windows-terminal" / "settings.json"
    if not wt_settings.exists():
        print(f"Error: {wt_settings} not found", file=sys.stderr)
        raise SystemExit(1)
    wt_data = json.loads(wt_settings.read_text(encoding="utf-8"))
    scheme_name = palette_name.replace("-", " ").title()
    mapping = {
        "black": "black",
        "red": "red",
        "green": "green",
        "yellow": "yellow",
        "blue": "blue",
        "purple": "purple",
        "cyan": "cyan",
        "white": "white",
        "bright_black": "brightBlack",
        "bright_red": "brightRed",
        "bright_green": "brightGreen",
        "bright_yellow": "brightYellow",
        "bright_blue": "brightBlue",
        "bright_purple": "brightPurple",
        "bright_cyan": "brightCyan",
        "bright_white": "brightWhite",
    }

    schemes = wt_data.setdefault("schemes", [])
    for scheme in schemes:
        if scheme.get("name") == scheme_name:
            target = scheme
            break
    else:
        target = {"name": scheme_name}
        schemes.append(target)

    for k, v in colors.items():
        target[mapping[k]] = v

    wt_profiles = wt_data.get("profiles", {})
    defaults = wt_profiles.setdefault("defaults", {})
    defaults["colorScheme"] = scheme_name

    for prof in wt_profiles.get("list", []):
        prof["colorScheme"] = scheme_name

    wt_settings.write_text(json.dumps(wt_data, indent=2) + "\n", encoding="utf-8")


def list_palettes(repo_root: Path) -> None:
    """Print available palette names."""
    for f in (repo_root / "palettes").glob("*.toml"):
        print(f.stem)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Terminal Harmony Manager")
    sub = parser.add_subparsers(dest="cmd", required=True)

    apply_cmd = sub.add_parser("apply", help="Apply a palette")
    apply_cmd.add_argument("palette")

    sub.add_parser("list-palettes", help="Show available palettes")

    args = parser.parse_args(argv)

    if args.cmd == "apply":
        apply_palette(args.palette, REPO_ROOT)
    elif args.cmd == "list-palettes":
        list_palettes(REPO_ROOT)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
