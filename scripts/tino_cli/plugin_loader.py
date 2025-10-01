"""Dynamic plug-in loader for :mod:`scripts.tino_cli`."""
from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator, List, Optional

import typer

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "plugin-registry.json"

@dataclass(slots=True)
class PluginCommand:
    """Representation of a plug-in provided CLI command."""

    plugin: str
    name: str
    help: str
    handler: Callable[[tuple[str, ...]], int]


def _load_registry(path: Path = REGISTRY_PATH) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _import_callable(qualname: str) -> Callable[[tuple[str, ...]], int] | None:
    module_name, _, attr = qualname.partition(":")
    if not module_name or not attr:
        return None
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return None
    func = getattr(module, attr, None)
    if callable(func):
        return func
    return None


def iter_plugin_commands() -> Iterator[PluginCommand]:
    """Yield :class:`PluginCommand` objects from ``plugin-registry.json``."""

    registry = _load_registry()
    plugins = registry.get("plugins")
    if not isinstance(plugins, dict):
        return
    for name, raw_meta in plugins.items():
        if isinstance(raw_meta, str):
            help_text = f"Commands for the {name} plug-in (install {raw_meta})."
            handler = _fallback_handler(name, raw_meta)
            yield PluginCommand(name=name, help=help_text, plugin=name, handler=handler)
            continue
        if not isinstance(raw_meta, dict):
            continue
        cli_meta = raw_meta.get("cli", {})
        help_text = cli_meta.get("help") if isinstance(cli_meta, dict) else None
        if not help_text:
            package = raw_meta.get("package", "unknown package")
            help_text = f"Commands for the {name} plug-in (install {package})."
        commands = []
        if isinstance(cli_meta, dict):
            commands = cli_meta.get("commands", [])
        if not commands:
            handler = _fallback_handler(name, raw_meta.get("package", "<unknown>"))
            yield PluginCommand(name=name, help=help_text, plugin=name, handler=handler)
            continue
        for command_meta in commands:
            if not isinstance(command_meta, dict):
                continue
            cmd_name = command_meta.get("name") or name
            cmd_help = command_meta.get("help") or help_text
            qualname = command_meta.get("callable")
            handler = _import_callable(qualname) if isinstance(qualname, str) else None
            if handler is None:
                package = raw_meta.get("package", "<unknown>")
                handler = _fallback_handler(name, package)
            yield PluginCommand(plugin=name, name=cmd_name, help=cmd_help, handler=handler)
    return


def _fallback_handler(plugin: str, package: str) -> Callable[[tuple[str, ...]], int]:
    def _handler(args: tuple[str, ...]) -> int:  # noqa: ARG001 - forwarded command
        typer.echo(
            f"The '{plugin}' plug-in is not installed. Install '{package}' to use this command.",
            err=True,
        )
        return 1

    return _handler


def register_plugin_commands(app: typer.Typer) -> None:
    """Attach plug-in commands to ``app`` under their plug-in names."""

    grouped: dict[str, list[PluginCommand]] = {}
    for command in iter_plugin_commands():
        grouped.setdefault(command.plugin, []).append(command)
    for plugin, commands in sorted(grouped.items()):
        help_text = commands[0].help if commands else f"Commands for plug-in {plugin}."
        plugin_app = typer.Typer(help=help_text)

        for command in commands:
            plugin_app.command(command.name, help=command.help)(_wrap_handler(command.handler))

        app.add_typer(plugin_app, name=plugin)


def _wrap_handler(handler: Callable[[tuple[str, ...]], int]) -> Callable[[List[str]], None]:
    def _command(
        args: Optional[List[str]] = typer.Argument(
            None,
            metavar="ARGS...",
            help="Arguments forwarded to the plug-in handler.",
            show_default=False,
        )
    ) -> None:
        forwarded = tuple(args or [])
        code = handler(forwarded)
        raise typer.Exit(code)

    return _command


__all__ = ["register_plugin_commands", "iter_plugin_commands", "PluginCommand"]
