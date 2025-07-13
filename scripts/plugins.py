#!/usr/bin/env python3
"""Manage LLM backend and recipe plug-ins."""

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
try:
    import jsonschema
except ImportError:  # pragma: no cover - optional dependency
    jsonschema = None

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "plugin-registry.schema.json"
if jsonschema is not None:
    try:
        with SCHEMA_PATH.open(encoding="utf-8") as fh:
            _REGISTRY_VALIDATOR = jsonschema.Draft202012Validator(json.load(fh))
    except Exception:
        _REGISTRY_VALIDATOR = None
else:  # pragma: no cover - optional dependency missing
    _REGISTRY_VALIDATOR = None

# Mapping of plug-in name to pip package used as a fallback when a registry
# cannot be loaded from the network or cache.
PLUGIN_REGISTRY: Dict[str, str] = {
    "sample": "d0ttino-sample-plugin",
    "openrouter": "d0ttino-openrouter-plugin",
    "lobechat": "d0ttino-lobechat-plugin",
    "mindbridge": "d0ttino-mindbridge-plugin",
}

# Mapping of recipe name to pip package used as a fallback when a registry
# cannot be loaded from the network or cache.
RECIPE_REGISTRY: Dict[str, str] = {
    "echo": "d0ttino-echo-recipe",
}

# Default directory for recipe packages downloaded via ``recipes sync``
RECIPE_DOWNLOAD_DIR = Path(__file__).resolve().parent / "recipes" / "packages"

# Default URL for downloading the plug-in registry
DEFAULT_REGISTRY_URL = "https://raw.githubusercontent.com/d0tTino/d0tTino/main/plugin-registry.json"


# Cache file for the remote registry
CACHE_PATH = Path.home() / ".cache" / "d0ttino" / "plugin_registry.json"

# Logger for plug-in management utilities
logger = logging.getLogger(__name__)


def _valid_registry(data: Dict[str, object]) -> bool:
    """Return True if ``data`` is a valid plug-in registry."""

    if _REGISTRY_VALIDATOR is not None:
        try:
            return bool(_REGISTRY_VALIDATOR.is_valid(data))
        except Exception:  # pragma: no cover - validator failure
            return False
    plugins = data.get("plugins")
    recipes = data.get("recipes")
    return (
        isinstance(plugins, dict)
        and all(isinstance(v, str) for v in plugins.values())
        and (
            recipes is None
            or (
                isinstance(recipes, dict)
                and all(isinstance(v, str) for v in recipes.values())
            )
        )
    )


def load_registry(section: str = "plugins", update: bool = False) -> Dict[str, str]:
    """Return the plug-in registry section from URL, cache or the built-in default.

    ``update`` forces a fresh download of the registry before falling back to the
    cached copy.
    """

    url = os.environ.get("PLUGIN_REGISTRY_URL", DEFAULT_REGISTRY_URL)

    data: Dict[str, object] | None = None

    if not update and CACHE_PATH.exists():
        try:
            with CACHE_PATH.open(encoding="utf-8") as fh:
                cached = json.load(fh)
            if isinstance(cached, dict) and _valid_registry(cached):
                data = cached
        except Exception:
            pass

    if data is None:
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            fetched = resp.json()
            if isinstance(fetched, dict) and _valid_registry(fetched):
                CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
                CACHE_PATH.write_text(json.dumps(fetched))
                data = fetched
        except requests.exceptions.RequestException as exc:
            logger.warning(
                "Failed to fetch plug-in registry from %s: %s. Using cached registry if available.",
                url,
                exc,
            )
        except Exception:
            pass

    if data is None and CACHE_PATH.exists():
        try:
            with CACHE_PATH.open(encoding="utf-8") as fh:
                cached = json.load(fh)
            if isinstance(cached, dict) and _valid_registry(cached):
                data = cached
        except Exception:
            pass

    if isinstance(data, dict):
        mapping = data.get(section) or {}
        if isinstance(mapping, dict):
            return {str(k): str(v) for k, v in mapping.items()}

    if section == "plugins":
        return PLUGIN_REGISTRY
    return RECIPE_REGISTRY


def _is_installed(package: str) -> bool:
    try:
        importlib.metadata.distribution(package)
        return True
    except importlib.metadata.PackageNotFoundError:
        return False


def _cmd_list_impl(section: str, update: bool) -> int:
    registry = load_registry(section, update=update)
    for name, package in sorted(registry.items()):
        status = "installed" if _is_installed(package) else "not installed"
        print(f"{name}\t({package}) - {status}")
    return 0


def _cmd_list_backends(args: argparse.Namespace) -> int:
    return _cmd_list_impl("plugins", args.update)


def _cmd_install_impl(args: argparse.Namespace, section: str) -> int:
    registry = load_registry(section, update=args.update)
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


def _cmd_install_backend(args: argparse.Namespace) -> int:
    return _cmd_install_impl(args, "plugins")


def _cmd_remove_impl(args: argparse.Namespace, section: str) -> int:
    registry = load_registry(section, update=args.update)
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


def _cmd_remove_backend(args: argparse.Namespace) -> int:
    return _cmd_remove_impl(args, "plugins")


def _cmd_list_recipes(args: argparse.Namespace) -> int:
    return _cmd_list_impl("recipes", args.update)


def _cmd_install_recipes(args: argparse.Namespace) -> int:
    return _cmd_install_impl(args, "recipes")


def _cmd_remove_recipes(args: argparse.Namespace) -> int:
    return _cmd_remove_impl(args, "recipes")


def _cmd_sync_recipes(args: argparse.Namespace) -> int:
    """Install recipe packages listed in the registry."""
    registry = load_registry("recipes", update=args.update)
    dest = Path(args.dest) if args.dest else RECIPE_DOWNLOAD_DIR
    dest.mkdir(parents=True, exist_ok=True)
    for pkg in registry.values():
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--no-deps",
                    "--target",
                    str(dest),
                    pkg,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            if exc.stderr:
                print(exc.stderr, file=sys.stderr, end="")
            return exc.returncode
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update",
        action="store_true",
        help="Force fresh download of the plug-in registry",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    backends = sub.add_parser("backends", help="Manage backend plug-ins")
    backend_sub = backends.add_subparsers(dest="backend_command", required=True)

    b_list = backend_sub.add_parser("list", help="List available backends")
    b_list.set_defaults(func=_cmd_list_backends)

    b_install = backend_sub.add_parser("install", help="Install a backend")
    b_install.add_argument("name", help="Backend name")
    b_install.set_defaults(func=_cmd_install_backend)

    b_remove = backend_sub.add_parser("remove", help="Remove a backend")
    b_remove.add_argument("name", help="Backend name")
    b_remove.set_defaults(func=_cmd_remove_backend)

    recipe = sub.add_parser("recipes", help="Manage recipe plug-ins")
    recipe_sub = recipe.add_subparsers(dest="recipe_command", required=True)

    r_list = recipe_sub.add_parser("list", help="List available recipes")
    r_list.set_defaults(func=_cmd_list_recipes)

    r_install = recipe_sub.add_parser("install", help="Install a recipe")
    r_install.add_argument("name", help="Recipe name")
    r_install.set_defaults(func=_cmd_install_recipes)

    r_remove = recipe_sub.add_parser("remove", help="Remove a recipe")
    r_remove.add_argument("name", help="Recipe name")
    r_remove.set_defaults(func=_cmd_remove_recipes)

    r_sync = recipe_sub.add_parser(
        "sync", help="Download and install recipe packages from the registry"
    )
    r_sync.add_argument(
        "--dest",
        help="Directory to install downloaded packages",
    )
    r_sync.set_defaults(func=_cmd_sync_recipes)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    if jsonschema is None:
        print(
            "jsonschema is required for plug-in management. Install it via 'pip install llm[cli]' or 'pip install jsonschema'.",
            file=sys.stderr,
        )
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

