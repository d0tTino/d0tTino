"""Dynamic plug-in loader for :mod:`scripts.tino_cli`."""
from __future__ import annotations

import importlib
import json
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator, List, Optional

import typer

from scripts import plugins
from telemetry import analytics_default, record_event

from .executor import execute_command
from .state import CLIState

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "plugin-registry.json"


@dataclass(slots=True)
class PluginCommand:
    """Representation of a plug-in provided CLI command."""

    plugin: str
    name: str
    help: str
    tags: tuple[str, ...] = ()
    examples: tuple[str, ...] = ()
    exec: str | None = None
    callable: str | None = None
    package: str | None = None


def _load_registry(path: Path | None = None) -> plugins.PluginRegistryData | None:
    path = path or REGISTRY_PATH
    if not path.exists():
        typer.echo(f"Plug-in registry not found at {path}.", err=True)
        record_event(
            "plugin_registry",
            {"status": "missing", "path": str(path)},
            enabled=analytics_default(),
        )
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        typer.echo(f"Failed to load plug-in registry at {path}: {exc}", err=True)
        record_event(
            "plugin_registry",
            {"status": "invalid", "reason": "read_error", "detail": str(exc)},
            enabled=analytics_default(),
        )
        return None
    try:
        plugins.validate_registry_payload(payload)
    except Exception as exc:
        detail = getattr(exc, "message", None) or str(exc)
        location = getattr(exc, "json_path", None) or getattr(exc, "path", None)
        context = f" at {location}" if location else ""
        typer.echo(
            f"Invalid plug-in registry schema{context}: {detail}.",
            err=True,
        )
        record_event(
            "plugin_registry",
            {
                "status": "invalid",
                "reason": "schema_validation",
                "detail": detail,
                "location": str(location) if location else None,
            },
            enabled=analytics_default(),
        )
        return None
    try:
        return plugins.parse_registry_payload(payload)
    except Exception as exc:
        typer.echo(f"Failed to parse plug-in registry: {exc}", err=True)
        record_event(
            "plugin_registry",
            {"status": "invalid", "reason": "parse_error", "detail": str(exc)},
            enabled=analytics_default(),
        )
    return None


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


def _normalise_args(args: Optional[List[str]], *, command_name: str | None = None) -> List[str]:
    values = list(args or [])
    if command_name and values and values[0] == command_name:
        values = values[1:]
    if values and values[0] == "--":
        values = values[1:]
    return values


def _resolve_state(ctx: typer.Context) -> CLIState | None:
    state = getattr(ctx, "obj", None)
    if isinstance(state, CLIState):
        return state
    return None


def _format_help(help_text: str, tags: tuple[str, ...], examples: tuple[str, ...]) -> str:
    sections: list[str] = []
    if tags:
        sections.append("Tags: " + ", ".join(tags))
    if examples:
        formatted = "\n".join(f"  {example}" for example in examples)
        sections.append(f"Examples:\n{formatted}")
    if sections:
        return f"{help_text}\n\n" + "\n\n".join(sections)
    return help_text


def _fallback_message(plugin: str, package: str | None) -> str:
    package_hint = package or "the corresponding package"
    return f"The '{plugin}' plug-in is not installed. Install '{package_hint}' to use this command."


def _wrap_callable(
    handler: Callable[[tuple[str, ...]], int], *, command_name: str | None = None
) -> Callable[[typer.Context, Optional[List[str]]], None]:
    def _command(
        ctx: typer.Context,
        args: Optional[List[str]] = typer.Argument(
            None,
            metavar="ARGS...",
            help="Arguments forwarded to the plug-in handler.",
            show_default=False,
        ),
    ) -> None:
        forwarded = tuple(_normalise_args(args, command_name=command_name))
        code = handler(forwarded)
        raise typer.Exit(code)

    return _command


def _wrap_exec(
    exec_command: str,
    *,
    require_confirm: bool = False,
    command_name: str | None = None,
) -> Callable[[typer.Context, Optional[List[str]]], None]:
    def _command(
        ctx: typer.Context,
        args: Optional[List[str]] = typer.Argument(
            None,
            metavar="ARGS...",
            help="Arguments forwarded to the plug-in command.",
            show_default=False,
        ),
    ) -> None:
        forwarded = _normalise_args(args, command_name=command_name)
        command = shlex.split(exec_command)
        command.extend(forwarded)
        state = _resolve_state(ctx)
        code = execute_command(command, state=state, require_confirm=require_confirm)
        raise typer.Exit(code)

    return _command


def _wrap_fallback(
    plugin: str,
    package: str | None,
    *,
    command_name: str | None = None,
) -> Callable[[typer.Context, Optional[List[str]]], None]:
    message = _fallback_message(plugin, package)

    def _command(
        ctx: typer.Context,
        args: Optional[List[str]] = typer.Argument(
            None,
            metavar="ARGS...",
            help="Arguments forwarded to the plug-in handler.",
            show_default=False,
        ),
    ) -> None:  # noqa: ARG001 - forwarded command
        _normalise_args(args, command_name=command_name)
        typer.echo(message, err=True)
        raise typer.Exit(1)

    return _command


def _plugin_help(plugin: str, package: plugins.PluginPackage) -> str:
    cli_meta = package.cli
    if cli_meta and cli_meta.help:
        return cli_meta.help
    return f"Commands for the {plugin} plug-in (install {package.package})."


def iter_plugin_commands() -> Iterator[PluginCommand]:
    """Yield :class:`PluginCommand` objects from ``plugin-registry.json``."""

    registry = _load_registry()
    if registry is None:
        return
    for name, package in registry.plugin_packages.items():
        cli_meta = package.cli
        if cli_meta is None or not cli_meta.commands:
            yield PluginCommand(
                plugin=name,
                name="install",
                help=_plugin_help(name, package),
                package=package.package,
            )
            continue
        for descriptor in cli_meta.commands:
            yield PluginCommand(
                plugin=name,
                name=descriptor.name,
                help=descriptor.help,
                tags=descriptor.tags,
                examples=descriptor.examples,
                exec=descriptor.exec,
                callable=descriptor.callable,
                package=package.package,
            )


def _register_registry_commands(app: typer.Typer, registry: plugins.PluginRegistryData) -> None:
    for descriptor in registry.commands:
        help_text = _format_help(descriptor.help, descriptor.tags, descriptor.examples)
        app.command(descriptor.name, help=help_text)(
            _wrap_exec(descriptor.exec, command_name=descriptor.name)
        )
        record_event(
            "plugin_command_registration",
            {"plugin": "registry", "command": descriptor.name, "status": "registered"},
            enabled=analytics_default(),
        )


def register_plugin_commands(app: typer.Typer) -> None:
    """Attach plug-in commands to ``app`` under their plug-in names."""

    registry = _load_registry()
    if registry is None:
        return

    _register_registry_commands(app, registry)

    for plugin, package in sorted(registry.plugin_packages.items()):
        plugin_app = typer.Typer(help=_plugin_help(plugin, package))
        cli_meta = package.cli
        commands = list(cli_meta.commands) if cli_meta else []
        if not commands:
            plugin_app.command("install", help=_fallback_message(plugin, package.package))(
                _wrap_fallback(plugin, package.package, command_name="install")
            )
            record_event(
                "plugin_command_registration",
                {
                    "plugin": plugin,
                    "command": "install",
                    "status": "fallback",
                    "reason": "no_cli_commands",
                },
                enabled=analytics_default(),
            )
            app.add_typer(plugin_app, name=plugin)
            continue
        for descriptor in commands:
            help_text = _format_help(descriptor.help, descriptor.tags, descriptor.examples)
            if descriptor.exec:
                plugin_app.command(descriptor.name, help=help_text)(
                    _wrap_exec(descriptor.exec, command_name=descriptor.name)
                )
                record_event(
                    "plugin_command_registration",
                    {
                        "plugin": plugin,
                        "command": descriptor.name,
                        "status": "registered",
                        "source": "exec",
                    },
                    enabled=analytics_default(),
                )
                continue
            handler = _import_callable(descriptor.callable) if descriptor.callable else None
            if handler is None:
                plugin_app.command(descriptor.name, help=help_text)(
                    _wrap_fallback(plugin, package.package, command_name=descriptor.name)
                )
                record_event(
                    "plugin_command_registration",
                    {
                        "plugin": plugin,
                        "command": descriptor.name,
                        "status": "skipped",
                        "reason": "missing_callable",
                    },
                    enabled=analytics_default(),
                )
                continue
            plugin_app.command(descriptor.name, help=help_text)(
                _wrap_callable(handler, command_name=descriptor.name)
            )
            record_event(
                "plugin_command_registration",
                {
                    "plugin": plugin,
                    "command": descriptor.name,
                    "status": "registered",
                    "source": "callable",
                },
                enabled=analytics_default(),
            )
        app.add_typer(plugin_app, name=plugin)


__all__ = ["register_plugin_commands", "iter_plugin_commands", "PluginCommand"]
