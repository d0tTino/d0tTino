import importlib
import json
import sys
from pathlib import Path
from typing import Any

import pytest


# Load Typer in isolation to satisfy plugin_loader import
_site_packages = (
    Path(sys.executable).resolve().parent.parent
    / "lib"
    / f"python{sys.version_info.major}.{sys.version_info.minor}"
    / "site-packages"
)
_typer_init = _site_packages / "typer" / "__init__.py"
_typer_spec = importlib.util.spec_from_file_location("typer", _typer_init)
if _typer_spec and _typer_spec.loader:
    _typer_module = importlib.util.module_from_spec(_typer_spec)
    _typer_spec.loader.exec_module(_typer_module)
    sys.modules["typer"] = _typer_module

import typer  # noqa: E402
from scripts.tino_cli import plugin_loader  # noqa: E402


@pytest.fixture()
def registry_path(tmp_path: Path) -> Path:
    return tmp_path / "registry.json"


def _write_registry(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _base_registry() -> dict[str, Any]:
    return {
        "name": "test-registry",
        "version": "1",
        "commands": [],
        "taskTemplates": [],
        "plugins": {},
        "recipes": {},
        "recipe_configs": {},
    }


def test_load_registry_reports_parse_errors(monkeypatch, registry_path: Path, capsys) -> None:
    registry_path.write_text("{not-json]", encoding="utf-8")
    events: list[dict[str, object]] = []

    monkeypatch.setattr(plugin_loader, "REGISTRY_PATH", registry_path)
    monkeypatch.setattr(plugin_loader, "analytics_default", lambda: True)
    monkeypatch.setattr(
        plugin_loader,
        "record_event",
        lambda _name, payload, *, enabled=False: events.append(payload),
    )

    assert plugin_loader._load_registry(registry_path) is None
    captured = capsys.readouterr()
    assert "Failed to load plug-in registry" in captured.err
    assert any(item.get("reason") == "read_error" for item in events)


def test_iter_plugin_commands_returns_empty_when_missing(monkeypatch, registry_path: Path, capsys) -> None:
    monkeypatch.setattr(plugin_loader, "REGISTRY_PATH", registry_path)
    monkeypatch.setattr(plugin_loader, "analytics_default", lambda: False)
    commands = list(plugin_loader.iter_plugin_commands())

    captured = capsys.readouterr()
    assert commands == []
    assert "Plug-in registry not found" in captured.err


def test_register_plugin_commands_uses_fallback_for_missing_callable(monkeypatch, registry_path: Path, tino_cli_runner) -> None:
    payload = _base_registry()
    payload["plugins"] = {
        "demo": {
            "package": "demo-package",
            "cli": {
                "commands": [
                    {
                        "name": "hello",
                        "help": "say hello",
                        "callable": "tests.missing:handler",
                    }
                ]
            },
        }
    }

    _write_registry(registry_path, payload)
    monkeypatch.setattr(plugin_loader, "REGISTRY_PATH", registry_path)
    monkeypatch.setattr(plugin_loader, "analytics_default", lambda: False)
    monkeypatch.setattr(plugin_loader, "record_event", lambda *_args, **_kwargs: None)

    app = typer.Typer()
    plugin_loader.register_plugin_commands(app)

    result = tino_cli_runner.invoke(app, ["demo", "hello"])

    assert result.exit_code == 1
    assert "The 'demo' plug-in is not installed" in result.stderr
