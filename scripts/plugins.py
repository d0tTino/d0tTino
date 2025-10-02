#!/usr/bin/env python3
"""Manage plug-ins, registry-provided commands, and task templates."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import logging
import os
import shlex
import subprocess
import sys
import time
from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional

import requests

try:
    import jsonschema
except ImportError:  # pragma: no cover - optional dependency
    jsonschema = None

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "plugin-registry.schema.json"
REGISTRY_PATH = REPO_ROOT / "plugin-registry.json"


@dataclass(frozen=True)
class PluginCommand:
    """Executable command contributed by a plug-in."""

    name: str
    help: str
    exec: str
    tags: tuple[str, ...] = ()
    examples: tuple[str, ...] = ()


@dataclass(frozen=True)
class TaskTemplateVariable:
    """Variable available for substitution in a task template."""

    name: str
    description: str
    required: bool = False
    type: str | None = None
    default: Any = None


@dataclass(frozen=True)
class TaskTemplateDescriptor:
    """Reusable task template exposed by the registry."""

    id: str
    name: str
    description: str
    prompt: str
    variables: tuple[TaskTemplateVariable, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PluginPackage:
    """Metadata describing an installable plug-in."""

    name: str
    package: str
    raw: Mapping[str, Any] = field(default_factory=dict)

    @property
    def mcp(self) -> Mapping[str, Any] | None:
        meta = self.raw.get("mcp") if isinstance(self.raw, Mapping) else None
        return meta if isinstance(meta, Mapping) else None

    def as_mapping(self) -> Dict[str, Any]:
        if isinstance(self.raw, Mapping) and self.raw:
            return deepcopy(dict(self.raw))
        return {"package": self.package}


@dataclass(frozen=True)
class PluginRegistryData:
    """Fully parsed plug-in registry payload."""

    name: str
    version: str
    description: str | None
    homepage: str | None
    commands: tuple[PluginCommand, ...]
    task_templates: tuple[TaskTemplateDescriptor, ...]
    plugin_packages: Mapping[str, PluginPackage]
    recipe_packages: Mapping[str, str]
    recipe_configs: Mapping[str, str]
    raw: Mapping[str, Any]

    @property
    def plugin_package_map(self) -> Dict[str, str]:
        return {name: pkg.package for name, pkg in self.plugin_packages.items()}

    @property
    def recipes_map(self) -> Dict[str, str]:
        return dict(self.recipe_packages)

    @property
    def mcp_plugins(self) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}
        for name, pkg in self.plugin_packages.items():
            meta = pkg.as_mapping()
            if "mcp" in meta:
                result[name] = meta
        return result

    def get_command(self, name: str) -> PluginCommand | None:
        return next((cmd for cmd in self.commands if cmd.name == name), None)


logger = logging.getLogger(__name__)

DEFAULT_REGISTRY_URL = (
    "https://raw.githubusercontent.com/d0tTino/d0tTino/main/plugin-registry.json"
)
CACHE_PATH = Path.home() / ".cache" / "d0ttino" / "plugin_registry.json"
MCP_CONFIG_PATH = Path.home() / ".config" / "d0tTino" / "mcp.json"
DEFAULT_CACHE_TTL = max(0, int(os.environ.get("PLUGIN_REGISTRY_TTL", "86400")))


if jsonschema is not None:
    try:
        with SCHEMA_PATH.open(encoding="utf-8") as fh:
            _REGISTRY_VALIDATOR = jsonschema.Draft202012Validator(json.load(fh))
    except Exception:  # pragma: no cover - fallback to runtime validation
        _REGISTRY_VALIDATOR = None
else:  # pragma: no cover - optional dependency missing
    _REGISTRY_VALIDATOR = None


def _load_local_registry() -> Dict[str, Any]:
    try:
        with REGISTRY_PATH.open(encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {
            "name": "d0tTino Local Registry",
            "version": "0",
            "commands": [],
            "taskTemplates": [],
            "plugins": {},
            "recipes": {},
            "recipe_configs": {},
        }


_DEFAULT_REGISTRY_RAW = _load_local_registry()


def _validate_registry(data: Mapping[str, Any]) -> None:
    if _REGISTRY_VALIDATOR is not None:
        _REGISTRY_VALIDATOR.validate(data)
        return
    required = ("name", "version", "commands", "taskTemplates")
    for field in required:
        if field not in data:
            raise ValueError(f"registry missing required field: {field}")


def _merge_sequence(
    base: Iterable[Mapping[str, Any]], override: Iterable[Mapping[str, Any]], key: str
) -> list[Dict[str, Any]]:
    merged: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    for item in base:
        value = item.get(key)
        if isinstance(value, str):
            merged[value] = deepcopy(dict(item))
    for item in override:
        value = item.get(key)
        if isinstance(value, str):
            merged[value] = deepcopy(dict(item))
    return list(merged.values())


def _merge_registry(
    base: Mapping[str, Any], override: Mapping[str, Any]
) -> Dict[str, Any]:
    if not override:
        return deepcopy(dict(base))
    merged: Dict[str, Any] = deepcopy(dict(base))
    list_keys = {"commands": "name", "taskTemplates": "id"}
    for key, value in override.items():
        if key in list_keys and isinstance(value, list):
            merged[key] = _merge_sequence(
                base.get(key, []) if isinstance(base.get(key), list) else [], value, list_keys[key]
            )
        elif isinstance(value, dict) and isinstance(base.get(key), dict):
            new_mapping: Dict[str, Any] = deepcopy(dict(base.get(key, {})))
            for inner_key, inner_val in value.items():
                new_mapping[inner_key] = deepcopy(inner_val)
            merged[key] = new_mapping
        else:
            merged[key] = deepcopy(value)
    return merged


def _load_cache() -> tuple[Dict[str, Any] | None, int | None]:
    if not CACHE_PATH.exists():
        return None, None
    try:
        with CACHE_PATH.open(encoding="utf-8") as fh:
            cached_raw = json.load(fh)
    except json.JSONDecodeError:
        logger.warning("Ignoring corrupt registry cache: %s", CACHE_PATH)
        try:
            CACHE_PATH.unlink()
        except Exception:  # pragma: no cover - best effort cleanup
            pass
        return None, None
    if isinstance(cached_raw, dict) and "registry" in cached_raw and "timestamp" in cached_raw:
        registry = cached_raw.get("registry")
        timestamp = cached_raw.get("timestamp")
        if isinstance(registry, dict) and isinstance(timestamp, int):
            return registry, timestamp
    if isinstance(cached_raw, dict):
        return cached_raw, int(CACHE_PATH.stat().st_mtime)
    return None, None


def _write_cache(data: Mapping[str, Any]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp": int(time.time()), "registry": deepcopy(dict(data))}
    CACHE_PATH.write_text(json.dumps(payload), encoding="utf-8")


def _fetch_registry(url: str) -> Dict[str, Any] | None:
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict):
            merged = _merge_registry(_DEFAULT_REGISTRY_RAW, payload)
            _validate_registry(merged)
            _write_cache(payload)
            return merged
    except requests.exceptions.RequestException as exc:
        logger.warning(
            "Failed to fetch plug-in registry from %s: %s. Using cached registry if available.",
            url,
            exc,
        )
    except Exception as exc:  # pragma: no cover - validation failure
        logger.warning("Discarding invalid registry payload: %s", exc)
    return None


def _parse_commands(data: Iterable[Mapping[str, Any]]) -> tuple[PluginCommand, ...]:
    commands: list[PluginCommand] = []
    for entry in data:
        name = entry.get("name")
        help_text = entry.get("help")
        exec_cmd = entry.get("exec")
        if not all(isinstance(val, str) and val for val in (name, help_text, exec_cmd)):
            continue
        tags = tuple(tag for tag in entry.get("tags", []) if isinstance(tag, str))
        examples = tuple(
            example for example in entry.get("examples", []) if isinstance(example, str)
        )
        commands.append(PluginCommand(name=name, help=help_text, exec=exec_cmd, tags=tags, examples=examples))
    return tuple(commands)


def _parse_variables(data: Iterable[Mapping[str, Any]]) -> tuple[TaskTemplateVariable, ...]:
    variables: list[TaskTemplateVariable] = []
    for entry in data:
        name = entry.get("name")
        description = entry.get("description")
        if not (isinstance(name, str) and isinstance(description, str)):
            continue
        variables.append(
            TaskTemplateVariable(
                name=name,
                description=description,
                required=bool(entry.get("required", False)),
                type=entry.get("type") if isinstance(entry.get("type"), str) else None,
                default=entry.get("default"),
            )
        )
    return tuple(variables)


def _parse_templates(data: Iterable[Mapping[str, Any]]) -> tuple[TaskTemplateDescriptor, ...]:
    templates: list[TaskTemplateDescriptor] = []
    for entry in data:
        template_id = entry.get("id")
        name = entry.get("name")
        description = entry.get("description")
        prompt = entry.get("prompt")
        if not all(isinstance(val, str) and val for val in (template_id, name, description, prompt)):
            continue
        metadata = (
            deepcopy(dict(entry.get("metadata")))
            if isinstance(entry.get("metadata"), Mapping)
            else {}
        )
        variables = _parse_variables(entry.get("variables", []) if isinstance(entry.get("variables"), list) else [])
        templates.append(
            TaskTemplateDescriptor(
                id=template_id,
                name=name,
                description=description,
                prompt=prompt,
                variables=variables,
                metadata=metadata,
            )
        )
    return tuple(templates)


def _parse_plugins(data: Mapping[str, Any]) -> Dict[str, PluginPackage]:
    parsed: Dict[str, PluginPackage] = {}
    for name, value in data.items():
        if isinstance(value, str):
            parsed[name] = PluginPackage(name=name, package=value, raw={"package": value})
        elif isinstance(value, Mapping):
            package_name = value.get("package")
            if isinstance(package_name, str):
                parsed[name] = PluginPackage(name=name, package=package_name, raw=deepcopy(dict(value)))
    return parsed


def _parse_registry(data: Mapping[str, Any]) -> PluginRegistryData:
    name = str(data.get("name", "d0tTino Registry"))
    version = str(data.get("version", "0"))
    description = data.get("description") if isinstance(data.get("description"), str) else None
    homepage = data.get("homepage") if isinstance(data.get("homepage"), str) else None
    commands = _parse_commands(data.get("commands", []) if isinstance(data.get("commands"), list) else [])
    templates = _parse_templates(
        data.get("taskTemplates", []) if isinstance(data.get("taskTemplates"), list) else []
    )
    plugins_section = (
        data.get("plugins") if isinstance(data.get("plugins"), Mapping) else {}
    )
    recipes_section = (
        data.get("recipes") if isinstance(data.get("recipes"), Mapping) else {}
    )
    recipe_configs = (
        data.get("recipe_configs") if isinstance(data.get("recipe_configs"), Mapping) else {}
    )
    return PluginRegistryData(
        name=name,
        version=version,
        description=description,
        homepage=homepage,
        commands=commands,
        task_templates=templates,
        plugin_packages=_parse_plugins(plugins_section),
        recipe_packages=deepcopy(dict(recipes_section)),
        recipe_configs=deepcopy(dict(recipe_configs)),
        raw=deepcopy(dict(data)),
    )


def load_registry(update: bool = False, ttl: int = DEFAULT_CACHE_TTL) -> PluginRegistryData:
    """Return the parsed plug-in registry data."""

    base_data = deepcopy(_DEFAULT_REGISTRY_RAW)
    _validate_registry(base_data)

    url = os.environ.get("PLUGIN_REGISTRY_URL", DEFAULT_REGISTRY_URL)
    cached_data, cached_ts = _load_cache()
    ttl = max(0, ttl)

    registry_payload: Mapping[str, Any] | None = None

    if update or cached_ts is None or ttl == 0 or time.time() - cached_ts > ttl:
        fetched = _fetch_registry(url)
        if fetched is not None:
            registry_payload = fetched
        elif cached_data is not None:
            registry_payload = _merge_registry(base_data, cached_data)
    elif cached_data is not None:
        registry_payload = _merge_registry(base_data, cached_data)

    if registry_payload is None:
        registry_payload = base_data
    else:
        try:
            _validate_registry(registry_payload)
        except Exception:
            registry_payload = base_data

    return _parse_registry(registry_payload)


def _is_installed(package: str) -> bool:
    try:
        importlib.metadata.distribution(package)
        return True
    except importlib.metadata.PackageNotFoundError:
        return False


def _load_mcp_config() -> Dict[str, Any]:
    try:
        return json.loads(MCP_CONFIG_PATH.read_text())
    except Exception:
        return {}


def _save_mcp_config(data: Mapping[str, Any]) -> None:
    MCP_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    MCP_CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _cmd_list_impl(args: argparse.Namespace, section: str) -> int:
    registry: PluginRegistryData = args.registry
    if section == "plugins":
        mapping = registry.plugin_package_map
    else:
        mapping = registry.recipes_map
    for name, package in sorted(mapping.items()):
        status = "installed" if _is_installed(package) else "not installed"
        print(f"{name}\t({package}) - {status}")
    return 0


def _cmd_list_backends(args: argparse.Namespace) -> int:
    return _cmd_list_impl(args, "plugins")


def _run_pip_action(
    args: argparse.Namespace, section: str, pip_args: list[str]
) -> int:
    registry: PluginRegistryData = args.registry
    mapping = registry.plugin_package_map if section == "plugins" else registry.recipes_map
    name = args.name
    if name not in mapping:
        print(f"Unknown plug-in: {name}", file=sys.stderr)
        return 1
    pkg = mapping[name]
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", *pip_args, pkg],
            check=True,
            capture_output=True,
            text=True,
        )
        return 0
    except subprocess.CalledProcessError as exc:
        if exc.stderr:
            print(exc.stderr, file=sys.stderr, end="")
        return exc.returncode


def _cmd_install_impl(args: argparse.Namespace, section: str) -> int:
    return _run_pip_action(args, section, ["install"])


def _cmd_install_backend(args: argparse.Namespace) -> int:
    return _cmd_install_impl(args, "plugins")


def _cmd_remove_impl(args: argparse.Namespace, section: str) -> int:
    return _run_pip_action(args, section, ["uninstall", "-y"])


def _cmd_remove_backend(args: argparse.Namespace) -> int:
    return _cmd_remove_impl(args, "plugins")


def _cmd_mcp_enable(args: argparse.Namespace) -> int:
    registry: PluginRegistryData = args.registry
    meta = registry.mcp_plugins.get(args.name)
    if not meta:
        print(f"Unknown MCP plug-in: {args.name}", file=sys.stderr)
        return 1
    descriptor = meta.get("mcp", {}).get("descriptor") if isinstance(meta.get("mcp"), Mapping) else None
    if not (isinstance(descriptor, Mapping) and descriptor.get("server_url")):
        print(f"No MCP descriptor for plug-in: {args.name}", file=sys.stderr)
        return 1
    config = _load_mcp_config()
    config[args.name] = descriptor
    _save_mcp_config(config)
    return 0


def _cmd_mcp_disable(args: argparse.Namespace) -> int:
    config = _load_mcp_config()
    if args.name in config:
        del config[args.name]
        _save_mcp_config(config)
        return 0
    print(f"MCP plug-in not enabled: {args.name}", file=sys.stderr)
    return 1


def _cmd_list_recipes(args: argparse.Namespace) -> int:
    return _cmd_list_impl(args, "recipes")


def _cmd_install_recipes(args: argparse.Namespace) -> int:
    return _cmd_install_impl(args, "recipes")


def _cmd_remove_recipes(args: argparse.Namespace) -> int:
    return _cmd_remove_impl(args, "recipes")


def _cmd_sync_recipes(args: argparse.Namespace) -> int:
    registry: PluginRegistryData = args.registry
    dest = Path(args.dest) if args.dest else REPO_ROOT / "scripts" / "recipes" / "packages"
    dest.mkdir(parents=True, exist_ok=True)
    for pkg in registry.recipes_map.values():
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


def _cmd_publish_recipes(args: argparse.Namespace) -> int:
    url = args.url or os.environ.get("PLUGIN_REGISTRY_UPLOAD_URL")
    if not url:
        print("Upload URL required (--url or PLUGIN_REGISTRY_UPLOAD_URL)", file=sys.stderr)
        return 1
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "twine",
                "upload",
                "--repository-url",
                url,
                args.path,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return 0
    except subprocess.CalledProcessError as exc:
        if exc.stderr:
            print(exc.stderr, file=sys.stderr, end="")
        return exc.returncode


def _cmd_commands_list(args: argparse.Namespace) -> int:
    registry: PluginRegistryData = args.registry
    if not registry.commands:
        print("No plug-in commands are registered.")
        return 0
    width = max(len(cmd.name) for cmd in registry.commands)
    for cmd in registry.commands:
        print(f"{cmd.name.ljust(width)}  {cmd.help}")
    return 0


def _cmd_commands_run(args: argparse.Namespace) -> int:
    registry: PluginRegistryData = args.registry
    descriptor = registry.get_command(args.name)
    if descriptor is None:
        print(f"Unknown plug-in command: {args.name}", file=sys.stderr)
        return 1
    cmdline = shlex.split(descriptor.exec)
    extra = args.args or []
    if extra and extra[0] == "--":
        extra = extra[1:]
    cmdline.extend(extra)
    try:
        subprocess.run(cmdline, check=True)
        return 0
    except subprocess.CalledProcessError as exc:
        return exc.returncode


def _format_epilog(registry: PluginRegistryData | None) -> str | None:
    if registry is None or not registry.commands:
        return None
    width = max(len(cmd.name) for cmd in registry.commands)
    lines = ["Available plug-in commands:"]
    for cmd in registry.commands:
        lines.append(f"  {cmd.name.ljust(width)}  {cmd.help}")
    lines.append("\nRun 'python scripts/plugins.py commands run <name> -- --extra' to execute a command.")
    return "\n".join(lines)


def build_parser(preview_registry: PluginRegistryData | None = None) -> argparse.ArgumentParser:
    if preview_registry is None:
        try:
            preview_registry = load_registry()
        except Exception:  # pragma: no cover - help should still render
            preview_registry = None
    parser = argparse.ArgumentParser(description=__doc__, epilog=_format_epilog(preview_registry))
    parser.add_argument(
        "--update",
        action="store_true",
        help="Force fresh download of the plug-in registry",
    )
    parser.add_argument(
        "--mcp",
        action="store_true",
        help="Serve MCP endpoints for registered plug-ins",
    )
    sub = parser.add_subparsers(dest="command")

    new = sub.add_parser("new", help="Scaffold a new plug-in")
    new.add_argument("name", help="Plug-in name")
    new.add_argument("--recipe", action="store_true", help="Create a recipe plug-in")
    new.add_argument("--description", default="A d0tTino plug-in")
    new.add_argument("--output", default=".", help="Output directory")
    new.set_defaults(func=_cmd_new_plugin)

    plugin_cmd = sub.add_parser("plugin", help="Manage MCP plug-ins")
    plugin_sub = plugin_cmd.add_subparsers(dest="plugin_command", required=True)

    p_new = plugin_sub.add_parser("new", help="Scaffold a new MCP plug-in")
    p_new.add_argument("name", help="Plug-in name")
    p_new.add_argument("--description", default="A d0tTino plug-in")
    p_new.add_argument("--output", default=".", help="Output directory")
    p_new.set_defaults(func=_cmd_plugin_new)

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

    mcp = sub.add_parser("mcp", help="Manage MCP tools")
    mcp_sub = mcp.add_subparsers(dest="mcp_command", required=True)

    m_enable = mcp_sub.add_parser("enable", help="Enable an MCP tool")
    m_enable.add_argument("name", help="Tool name")
    m_enable.set_defaults(func=_cmd_mcp_enable)

    m_disable = mcp_sub.add_parser("disable", help="Disable an MCP tool")
    m_disable.add_argument("name", help="Tool name")
    m_disable.set_defaults(func=_cmd_mcp_disable)

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

    r_publish = recipe_sub.add_parser(
        "publish", help="Upload a recipe package to a registry"
    )
    r_publish.add_argument("path", help="Path to recipe package")
    r_publish.add_argument(
        "--url",
        default=os.environ.get("PLUGIN_REGISTRY_UPLOAD_URL"),
        help="Registry URL for upload (default: PLUGIN_REGISTRY_UPLOAD_URL)",
    )
    r_publish.set_defaults(func=_cmd_publish_recipes)

    commands_parser = sub.add_parser("commands", help="List and run plug-in commands")
    commands_sub = commands_parser.add_subparsers(dest="commands_command", required=True)

    c_list = commands_sub.add_parser("list", help="List plug-in commands")
    c_list.set_defaults(func=_cmd_commands_list)

    c_run = commands_sub.add_parser(
        "run",
        help="Execute a plug-in command. Pass '--' to forward additional arguments.",
    )
    c_run.add_argument("name", help="Command name")
    c_run.add_argument("args", nargs=argparse.REMAINDER)
    c_run.set_defaults(func=_cmd_commands_run)

    return parser


def _cmd_new_plugin(args: argparse.Namespace) -> int:
    from scripts import plugin_scaffold

    plugin_scaffold.scaffold_plugin(
        args.name,
        recipe=args.recipe,
        description=args.description,
        output=args.output,
    )
    return 0


def _cmd_plugin_new(args: argparse.Namespace) -> int:
    from scripts import plugin_scaffold

    plugin_scaffold.scaffold_plugin(
        args.name,
        description=args.description,
        output=args.output,
    )
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    if jsonschema is None:
        print(
            "jsonschema is required for plug-in management. Install it via 'pip install llm[cli]' or 'pip install jsonschema'.",
            file=sys.stderr,
        )
    parser = build_parser()
    args = parser.parse_args(argv)

    registry = load_registry(update=getattr(args, "update", False))
    setattr(args, "registry", registry)

    if getattr(args, "mcp", False):
        from plugins import mcp_adapter

        mcp_adapter.serve(registry.mcp_plugins)
        return 0

    if not hasattr(args, "func"):
        parser.error("a command is required")
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
