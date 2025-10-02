from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from scripts import plugins


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
    assert "sample" in registry.plugin_package_map
