#!/usr/bin/env python3
"""Manage LLM backend plug-ins."""

from __future__ import annotations

import argparse
import importlib.metadata
import subprocess
import sys
from typing import Dict, List, Optional

# Mapping of plug-in name to pip package
PLUGIN_REGISTRY: Dict[str, str] = {
    "sample": "d0ttino-sample-plugin",
}


def _is_installed(package: str) -> bool:
    try:
        importlib.metadata.distribution(package)
        return True
    except importlib.metadata.PackageNotFoundError:
        return False


def _cmd_list(args: argparse.Namespace) -> int:
    for name, package in sorted(PLUGIN_REGISTRY.items()):
        status = "installed" if _is_installed(package) else "not installed"
        print(f"{name}\t({package}) - {status}")
    return 0


def _cmd_install(args: argparse.Namespace) -> int:
    name = args.name
    if name not in PLUGIN_REGISTRY:
        print(f"Unknown plug-in: {name}", file=sys.stderr)
        return 1
    pkg = PLUGIN_REGISTRY[name]
    result = subprocess.run([sys.executable, "-m", "pip", "install", pkg])
    return result.returncode


def _cmd_remove(args: argparse.Namespace) -> int:
    name = args.name
    if name not in PLUGIN_REGISTRY:
        print(f"Unknown plug-in: {name}", file=sys.stderr)
        return 1
    pkg = PLUGIN_REGISTRY[name]
    result = subprocess.run(
        [sys.executable, "-m", "pip", "uninstall", "-y", pkg]
    )
    return result.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    list_cmd = sub.add_parser("list", help="List available plug-ins")
    list_cmd.set_defaults(func=_cmd_list)

    install_cmd = sub.add_parser("install", help="Install a plug-in")
    install_cmd.add_argument("name", help="Plug-in name")
    install_cmd.set_defaults(func=_cmd_install)

    remove_cmd = sub.add_parser("remove", help="Remove a plug-in")
    remove_cmd.add_argument("name", help="Plug-in name")
    remove_cmd.set_defaults(func=_cmd_remove)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

