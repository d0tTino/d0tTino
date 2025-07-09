#!/usr/bin/env python3
"""Manage LLM backend plug-ins."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
from typing import Dict, List, Optional

import requests
import jsonschema

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "plugin-registry.schema.json"
try:
    with SCHEMA_PATH.open(encoding="utf-8") as fh:
        _REGISTRY_VALIDATOR = jsonschema.Draft202012Validator(json.load(fh))
except Exception:
    _REGISTRY_VALIDATOR = None

# Mapping of plug-in name to pip package used as a fallback when a registry
# cannot be loaded from the network or cache.
PLUGIN_REGISTRY: Dict[str, str] = {
    "sample": "d0ttino-sample-plugin",
}

# Cache file for the remote registry
CACHE_PATH = Path.home() / ".cache" / "d0ttino" / "plugin_registry.json"

# Logger for plug-in management utilities
logger = logging.getLogger(__name__)


def load_registry() -> Dict[str, str]:
    """Return the plug-in registry from URL, cache or the built-in default."""

    url = os.environ.get("PLUGIN_REGISTRY_URL")
    if url:
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict) and (
                _REGISTRY_VALIDATOR is None or _REGISTRY_VALIDATOR.is_valid(data)
            ):
                CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
                CACHE_PATH.write_text(json.dumps(data))
                return {str(k): str(v) for k, v in data.items()}
        except requests.exceptions.RequestException as exc:
            logger.warning("Failed to fetch plug-in registry from %s: %s", url, exc)
        except Exception:
            pass

    if CACHE_PATH.exists():
        try:
            with CACHE_PATH.open(encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict) and (
                _REGISTRY_VALIDATOR is None or _REGISTRY_VALIDATOR.is_valid(data)
            ):
                return {str(k): str(v) for k, v in data.items()}
        except Exception:
            pass

    return PLUGIN_REGISTRY


def _is_installed(package: str) -> bool:
    try:
        importlib.metadata.distribution(package)
        return True
    except importlib.metadata.PackageNotFoundError:
        return False


def _cmd_list(args: argparse.Namespace) -> int:
    registry = load_registry()
    for name, package in sorted(registry.items()):
        status = "installed" if _is_installed(package) else "not installed"
        print(f"{name}\t({package}) - {status}")
    return 0


def _cmd_install(args: argparse.Namespace) -> int:
    registry = load_registry()
    name = args.name
    if name not in registry:
        print(f"Unknown plug-in: {name}", file=sys.stderr)
        return 1
    pkg = registry[name]
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg],
            check=True,
            capture_output=True,
            text=True,
        )
        return 0
    except subprocess.CalledProcessError as e:
        if e.stderr:
            print(e.stderr, file=sys.stderr, end="")
        return e.returncode


def _cmd_remove(args: argparse.Namespace) -> int:
    registry = load_registry()
    name = args.name
    if name not in registry:
        print(f"Unknown plug-in: {name}", file=sys.stderr)
        return 1
    pkg = registry[name]
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", pkg],
            check=True,
            capture_output=True,
            text=True,
        )
        return 0
    except subprocess.CalledProcessError as e:
        if e.stderr:
            print(e.stderr, file=sys.stderr, end="")
        return e.returncode


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

