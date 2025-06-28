#!/usr/bin/env python3
"""Terminal Harmony Manager: sync palettes across tools."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib


REPO_ROOT = Path(__file__).resolve().parent.parent
PALETTES_DIR = REPO_ROOT / "palettes"


def load_palette(palette_path: Path) -> dict:
    """Load and return the palette dict from ``palette_path``."""
    with palette_path.open("rb") as f:
        return tomllib.load(f)


def apply_palette(palette_name: str, repo_root: Path) -> None:
    """Apply ``palette_name`` to Starship and Windows Terminal.

    This is currently a placeholder that prints out which palette would be
    applied. Future implementations will update ``starship.toml`` and the
    Windows Terminal ``settings.json`` file.
    """
    palette_file = repo_root / "palettes" / f"{palette_name}.toml"
    colors = load_palette(palette_file)[palette_name]
    print(f"Applying palette {palette_name} with {len(colors)} colors")
    # TODO: Update starship.toml and windows-terminal/settings.json


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
