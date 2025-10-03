import json
import time
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import typer

from scripts import plugins
from scripts.tino_cli import plugin_loader
from tests import stubs

if TYPE_CHECKING:
    from typer.testing import CliRunner


pytest.importorskip("requests")


def _registry_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "test-registry",
        "version": "1",
        "commands": [],
        "taskTemplates": [],
        "plugins": {},
        "recipes": {},
        "recipe_configs": {},
    }
    payload.update(overrides)
    return payload


def test_load_registry_returns_commands_and_templates() -> None:
    registry = plugins.load_registry()
    assert isinstance(registry, plugins.PluginRegistryData)
    assert any(cmd.name == "aiga:deploy" for cmd in registry.commands)
    assert any(tpl.id == "weekly-review" for tpl in registry.task_templates)
    assert "anthropic" in registry.plugin_package_map


def test_load_registry_uses_cache_when_offline(monkeypatch, tmp_path: Path) -> None:
    cache = tmp_path / "cache.json"
    monkeypatch.setattr(plugins, "CACHE_PATH", cache)

    cached_payload = {
        "timestamp": int(time.time()),
        "registry": {
            "name": "cached",
            "version": "1",
            "commands": [
                {"name": "cached:cmd", "help": "Cached command", "exec": "echo cached"}
            ],
            "taskTemplates": [],
            "plugins": {},
            "recipes": {},
            "recipe_configs": {},
        },
    }
    cache.write_text(json.dumps(cached_payload), encoding="utf-8")

    monkeypatch.setattr(
        plugins.requests,
        "get",
        lambda *a, **k: pytest.fail("network should not be called"),
    )

    registry = plugins.load_registry(ttl=3600)
    assert any(cmd.name == "cached:cmd" for cmd in registry.commands)


def test_load_registry_defaults_without_cache(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(plugins, "CACHE_PATH", tmp_path / "missing.json")

    def raise_exc(*_args, **_kwargs):
        raise plugins.requests.exceptions.RequestException("boom")

    monkeypatch.setattr(plugins.requests, "get", raise_exc)

    registry = plugins.load_registry()
    assert "sample" in registry.plugin_package_map


def test_load_registry_update_forces_fetch(monkeypatch, tmp_path: Path) -> None:
    cache = tmp_path / "cache.json"
    monkeypatch.setattr(plugins, "CACHE_PATH", cache)

    called: dict[str, bool] = {"fetch": False}

    def fake_fetch(url: str) -> dict[str, object] | None:
        called["fetch"] = True
        return {
            "name": "updated",
            "version": "1",
            "commands": [
                {"name": "updated:cmd", "help": "Updated command", "exec": "echo hi"}
            ],
            "taskTemplates": [],
            "plugins": {},
            "recipes": {},
            "recipe_configs": {},
        }

    monkeypatch.setattr(plugins, "_fetch_registry", fake_fetch)

    registry = plugins.load_registry(update=True)
    assert called["fetch"]
    assert any(cmd.name == "updated:cmd" for cmd in registry.commands)


def test_load_registry_invalid_cache_falls_back(monkeypatch, tmp_path: Path) -> None:
    cache = tmp_path / "cache.json"
    cache.write_text(json.dumps({"timestamp": int(time.time()), "registry": {"name": "bad"}}))
    monkeypatch.setattr(plugins, "CACHE_PATH", cache)

    def raise_exc(*_args, **_kwargs):
        raise plugins.requests.exceptions.RequestException("boom")

    monkeypatch.setattr(plugins.requests, "get", raise_exc)

    registry = plugins.load_registry()
    expected = {
        "anthropic": "d0ttino-anthropic-plugin",
        "mistral": "d0ttino-mistral-plugin",
        "lmql": "d0ttino-lmql-plugin",
    }
    for name, pkg in expected.items():
        assert registry.plugin_package_map[name] == pkg


def test_valid_registry_rejects_bad_descriptor():
    invalid = {
        "plugins": {
            "demo": {
                "package": "demo",  # minimal metadata
                "mcp": {"descriptor": "not-a-mapping"},
            }
        }
    }
    assert plugins._valid_registry(invalid) is False


def test_register_plugin_commands_executes_handler(
    tino_cli_runner: "CliRunner",
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    registry_path = tmp_path / "registry.json"
    registry = _registry_payload(
        plugins={
            "demo": {
                "package": "demo-pkg",
                "cli": {
                    "help": "Demo plug-in",
                    "commands": [
                        {
                            "name": "hello",
                            "help": "Say hello",
                            "callable": "tests.stubs:plugin_command",
                        }
                    ],
                },
            }
        }
    )
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    monkeypatch.setattr(plugin_loader, "REGISTRY_PATH", registry_path)
    registry_data = plugins.parse_registry_payload(registry)
    monkeypatch.setattr(plugin_loader, "_load_registry", lambda path=registry_path: registry_data)
    # Ensure stale call history from other tests does not leak in.
    stubs.plugin_command.calls = []  # type: ignore[attr-defined]

    app = typer.Typer()
    plugin_loader.register_plugin_commands(app)

    result = tino_cli_runner.invoke(app, ["demo", "hello", "alpha", "beta"])
    assert result.exit_code == 0
    assert stubs.plugin_command.calls[-1] == ("alpha", "beta")  # type: ignore[index]


def test_register_plugin_command_falls_back_on_missing_callable(
    tino_cli_runner: "CliRunner",
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    registry_path = tmp_path / "registry.json"
    registry = _registry_payload(
        plugins={
            "demo": {
                "package": "demo-pkg",
                "cli": {
                    "commands": [
                        {"name": "hello", "help": "Missing handler", "callable": "missing.module:run"}
                    ]
                },
            }
        }
    )
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    monkeypatch.setattr(plugin_loader, "REGISTRY_PATH", registry_path)
    registry_data = plugins.parse_registry_payload(registry)
    monkeypatch.setattr(plugin_loader, "_load_registry", lambda path=registry_path: registry_data)

    app = typer.Typer()
    plugin_loader.register_plugin_commands(app)

    result = tino_cli_runner.invoke(app, ["demo", "hello"])
    assert result.exit_code == 1
    assert "demo-pkg" in result.stderr or "demo-pkg" in result.output


def test_plugins_cli_runs_exec_command(
    tino_cli_runner: "CliRunner",
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = _registry_payload(
        commands=[
            {
                "name": "demo:exec",
                "help": "Demo exec",
                "exec": "echo demo",
                "tags": ["demo"],
                "examples": ["tino plugins demo:exec -- --flag value"],
            }
        ],
        plugins={},
    )
    registry_data = plugins.parse_registry_payload(registry)
    monkeypatch.setattr(plugin_loader, "_load_registry", lambda *_: registry_data)

    calls: dict[str, object] = {}

    def fake_execute(command, *, state=None, require_confirm=False):
        calls["command"] = list(command)
        calls["state"] = state
        calls["confirm"] = require_confirm
        return 0

    monkeypatch.setattr(plugin_loader, "execute_command", fake_execute)

    app = typer.Typer()
    plugin_loader.register_plugin_commands(app)

    result = tino_cli_runner.invoke(app, ["demo:exec", "--", "--flag", "value"])
    assert result.exit_code == 0
    assert calls["command"] == ["echo", "demo", "--flag", "value"]
    assert calls["state"] is None
    assert calls["confirm"] is False

