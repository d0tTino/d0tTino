from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest

from scripts import plugins


def _registry(
    *,
    plugins_map: dict[str, plugins.PluginPackage | str] | None = None,
    recipes: dict[str, str] | None = None,
    commands: tuple[plugins.PluginCommand, ...] | None = None,
) -> plugins.PluginRegistryData:
    plugin_packages: dict[str, plugins.PluginPackage] = {}
    for name, value in (plugins_map or {}).items():
        if isinstance(value, plugins.PluginPackage):
            plugin_packages[name] = value
        else:
            plugin_packages[name] = plugins.PluginPackage(
                name=name, package=value, raw={"package": value}
            )
    return plugins.PluginRegistryData(
        name="test",
        version="1",
        description=None,
        homepage=None,
        commands=commands or (),
        task_templates=(),
        plugin_packages=plugin_packages,
        recipe_packages=recipes or {},
        recipe_configs={},
        raw={},
    )


def test_list_outputs_available_plugins(monkeypatch, capsys):
    reg = _registry(plugins_map={"dummy": "dummy-pkg"})
    monkeypatch.setattr(plugins, "load_registry", lambda *a, **k: reg)
    monkeypatch.setattr(plugins, "_is_installed", lambda pkg: False)
    rc = plugins.main(["backends", "list"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert "dummy" in captured


def test_install_runs_pip(monkeypatch):
    reg = _registry(plugins_map={"dummy": "dummy-pkg"})
    calls: dict[str, object] = {}

    def fake_run(cmd, *args, **kwargs):
        calls["cmd"] = cmd
        calls["kwargs"] = kwargs

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(plugins.subprocess, "run", fake_run)
    monkeypatch.setattr(plugins, "load_registry", lambda *a, **k: reg)
    rc = plugins.main(["backends", "install", "dummy"])
    assert rc == 0
    assert calls["cmd"][0] == sys.executable
    assert "dummy-pkg" in calls["cmd"]
    assert calls["kwargs"].get("check")


def test_remove_runs_pip(monkeypatch):
    reg = _registry(plugins_map={"dummy": "dummy-pkg"})
    calls: dict[str, object] = {}

    def fake_run(cmd, *args, **kwargs):
        calls["cmd"] = cmd
        calls["kwargs"] = kwargs

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(plugins.subprocess, "run", fake_run)
    monkeypatch.setattr(plugins, "load_registry", lambda *a, **k: reg)
    rc = plugins.main(["backends", "remove", "dummy"])
    assert rc == 0
    assert calls["cmd"][0] == sys.executable
    assert "dummy-pkg" in calls["cmd"]


def test_install_failure_propagates(monkeypatch, capsys):
    reg = _registry(plugins_map={"dummy": "dummy-pkg"})

    def fake_run(cmd, *args, **kwargs):
        raise plugins.subprocess.CalledProcessError(5, cmd, stderr="fail\n")

    monkeypatch.setattr(plugins.subprocess, "run", fake_run)
    monkeypatch.setattr(plugins, "load_registry", lambda *a, **k: reg)
    rc = plugins.main(["backends", "install", "dummy"])
    captured = capsys.readouterr()
    assert rc == 5
    assert "fail" in captured.err


def test_main_warns_when_jsonschema_missing(monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "jsonschema", None)
    import importlib

    reloaded = importlib.reload(plugins)
    reg = _registry(plugins_map={"dummy": "pkg"})
    monkeypatch.setattr(reloaded, "load_registry", lambda *a, **k: reg)
    monkeypatch.setattr(reloaded, "_is_installed", lambda pkg: False)
    rc = reloaded.main(["backends", "list"])
    out = capsys.readouterr()
    assert rc == 0
    assert "jsonschema is required" in out.err


def test_recipe_list(monkeypatch, capsys):
    reg = _registry(recipes={"echo": "pkg"})
    monkeypatch.setattr(plugins, "load_registry", lambda *a, **k: reg)
    monkeypatch.setattr(plugins, "_is_installed", lambda pkg: False)
    rc = plugins.main(["recipes", "list"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "echo" in out


def test_recipe_install(monkeypatch):
    reg = _registry(recipes={"echo": "pkg"})
    calls: dict[str, object] = {}

    def fake_run(cmd, *args, **kwargs):
        calls["cmd"] = cmd

        class Res:
            returncode = 0

        return Res()

    monkeypatch.setattr(plugins.subprocess, "run", fake_run)
    monkeypatch.setattr(plugins, "load_registry", lambda *a, **k: reg)
    rc = plugins.main(["recipes", "install", "echo"])
    assert rc == 0
    assert "pkg" in calls["cmd"]


def test_recipe_sync(monkeypatch, tmp_path):
    reg = _registry(recipes={"echo": "pkg"})
    executed: list[list[str]] = []

    def fake_run(cmd, *args, **kwargs):
        executed.append(cmd)

        class Res:
            returncode = 0

        return Res()

    monkeypatch.setattr(plugins.subprocess, "run", fake_run)
    monkeypatch.setattr(plugins, "load_registry", lambda *a, **k: reg)
    rc = plugins.main(["recipes", "sync", "--dest", str(tmp_path)])
    assert rc == 0
    assert executed
    assert "pkg" in executed[0]


def test_commands_list_and_run(monkeypatch, capsys):
    command = plugins.PluginCommand(name="demo:cmd", help="Demo", exec="echo hi")
    reg = _registry(commands=(command,))

    monkeypatch.setattr(plugins, "load_registry", lambda *a, **k: reg)

    rc_list = plugins.main(["commands", "list"])
    out = capsys.readouterr().out
    assert rc_list == 0
    assert "demo:cmd" in out

    called: dict[str, object] = {}

    def fake_run(cmd, check=True):
        called["cmd"] = cmd

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(plugins.subprocess, "run", fake_run)
    rc_run = plugins.main(["commands", "run", "demo:cmd", "--", "--dry"])
    assert rc_run == 0
    assert called["cmd"][-1] == "--dry"


def test_mcp_flag_starts_server(monkeypatch):
    reg = _registry(plugins_map={})
    monkeypatch.setattr(plugins, "load_registry", lambda *a, **k: reg)

    called: dict[str, object] = {}

    from plugins import mcp_adapter

    monkeypatch.setattr(mcp_adapter, "serve", lambda registry_data: called.setdefault("registry", registry_data))

    rc = plugins.main(["--mcp"])
    assert rc == 0
    assert "registry" in called


def test_mcp_enable_writes_config(monkeypatch, tmp_path):
    cfg = tmp_path / "mcp.json"
    package = plugins.PluginPackage(
        name="dummy",
        package="pkg",
        raw={
            "package": "pkg",
            "mcp": {"descriptor": {"server_url": "https://example.com", "capabilities": []}},
        },
    )
    reg = _registry(plugins_map={"dummy": package})
    monkeypatch.setattr(plugins, "MCP_CONFIG_PATH", cfg)
    monkeypatch.setattr(plugins, "load_registry", lambda *a, **k: reg)
    rc = plugins.main(["mcp", "enable", "dummy"])
    assert rc == 0
    data = json.loads(cfg.read_text())
    assert data["dummy"]["server_url"] == "https://example.com"


def test_mcp_disable_removes_config(monkeypatch, tmp_path):
    cfg = tmp_path / "mcp.json"
    cfg.write_text(json.dumps({"dummy": {"server_url": "u", "capabilities": []}}))
    reg = _registry()
    monkeypatch.setattr(plugins, "MCP_CONFIG_PATH", cfg)
    monkeypatch.setattr(plugins, "load_registry", lambda *a, **k: reg)
    rc = plugins.main(["mcp", "disable", "dummy"])
    assert rc == 0
    assert json.loads(cfg.read_text()) == {}
