from __future__ import annotations

import argparse
from pathlib import Path

import pytest

pytest.importorskip("requests")

from scripts import plugins


def _make_registry(
    *,
    commands: tuple[plugins.PluginCommand, ...] | None = None,
    recipes: dict[str, str] | None = None,
    plugins_map: dict[str, plugins.PluginPackage] | None = None,
) -> plugins.PluginRegistryData:
    return plugins.PluginRegistryData(
        name="test",
        version="1",
        description=None,
        homepage=None,
        commands=commands or (),
        task_templates=(),
        plugin_packages=plugins_map or {},
        recipe_packages=recipes or {},
        recipe_configs={},
        raw={},
    )


def test_cmd_sync_recipes_uses_default_dir(monkeypatch, tmp_path: Path) -> None:
    registry = _make_registry(recipes={"echo": "echo-pkg", "foo": "foo-pkg"})

    executed: list[list[str]] = []

    def fake_run(cmd, *args, **kwargs):
        executed.append(cmd)

        class Res:
            returncode = 0

        return Res()

    monkeypatch.setattr(plugins.subprocess, "run", fake_run)
    args = argparse.Namespace(dest=str(tmp_path), registry=registry)
    rc = plugins._cmd_sync_recipes(args)
    assert rc == 0
    assert executed
    for call in executed:
        assert "--target" in call
        assert call[call.index("--target") + 1] == str(tmp_path)
        assert call[-1] in registry.recipes_map.values()


def test_build_parser_includes_command_epilog() -> None:
    registry = _make_registry(
        commands=(
            plugins.PluginCommand(name="demo:cmd", help="Demo command", exec="echo hi"),
        )
    )
    parser = plugins.build_parser(preview_registry=registry)
    assert "demo:cmd" in (parser.epilog or "")


def test_commands_run_executes_descriptor(monkeypatch) -> None:
    command = plugins.PluginCommand(name="demo:cmd", help="Demo", exec="echo base")
    registry = _make_registry(commands=(command,))

    called: dict[str, list[list[str]]] = {"commands": []}

    def fake_run(cmd, check=True):
        called["commands"].append(cmd)
        class Result:
            returncode = 0
        return Result()

    monkeypatch.setattr(plugins.subprocess, "run", fake_run)

    args = argparse.Namespace(name="demo:cmd", args=["--", "--flag"], registry=registry)
    rc = plugins._cmd_commands_run(args)
    assert rc == 0
    assert called["commands"][0][-1] == "--flag"


def test_commands_run_reports_unknown_command(monkeypatch) -> None:
    registry = _make_registry()
    args = argparse.Namespace(name="missing", args=[], registry=registry)
    rc = plugins._cmd_commands_run(args)
    assert rc == 1


def test_mcp_enable_requires_descriptor(monkeypatch) -> None:
    broken_pkg = plugins.PluginPackage(name="broken", package="pkg", raw={"package": "pkg"})
    registry = _make_registry(plugins_map={"broken": broken_pkg})
    args = argparse.Namespace(name="broken", registry=registry)
    rc = plugins._cmd_mcp_enable(args)
    assert rc == 1
