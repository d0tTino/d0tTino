#!/usr/bin/env python3
"""Validate that declared Neovim plugins are present in lazy-lock.json."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PLUGIN_RE = re.compile(r'"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"\s*,')


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def declared_plugins(plugins_dir: Path) -> dict[str, set[str]]:
    declared: dict[str, set[str]] = {}

    for plugin_file in sorted(plugins_dir.glob("*.lua")):
        content = plugin_file.read_text(encoding="utf-8")
        for owner_repo in sorted(set(PLUGIN_RE.findall(content))):
            short_name = owner_repo.rsplit("/", 1)[-1]
            declared.setdefault(short_name, set()).add(owner_repo)

    return declared


def parse_args() -> argparse.Namespace:
    root = repo_root()
    default_plugins_dir = root / "dotfiles" / "nvim" / ".config" / "nvim" / "lua" / "plugins"
    default_lockfile = root / "dotfiles" / "nvim" / ".config" / "nvim" / "lazy-lock.json"

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugins-dir", type=Path, default=default_plugins_dir)
    parser.add_argument("--lockfile", type=Path, default=default_lockfile)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plugins_dir = args.plugins_dir
    lockfile_path = args.lockfile

    if not plugins_dir.is_dir():
        print(f"error: plugin directory not found: {plugins_dir}", file=sys.stderr)
        return 1

    if not lockfile_path.is_file():
        print(f"error: lockfile not found: {lockfile_path}", file=sys.stderr)
        return 1

    declared = declared_plugins(plugins_dir)
    lock_data = json.loads(lockfile_path.read_text(encoding="utf-8"))
    lock_names = set(lock_data.keys())

    missing = sorted(name for name in declared if name not in lock_names)
    if missing:
        print("Neovim lazy-lock.json is missing declared plugins:", file=sys.stderr)
        for name in missing:
            repos = ", ".join(sorted(declared[name]))
            print(f"  - {name} ({repos})", file=sys.stderr)
        print(
            "\nRefresh lockfile intentionally with: ./scripts/setup-nvim.sh --refresh-lockfile",
            file=sys.stderr,
        )
        return 1

    print(f"Lockfile coverage OK: {len(declared)} declared plugins are pinned.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
