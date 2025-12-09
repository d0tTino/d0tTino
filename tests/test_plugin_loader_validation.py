import importlib.util
import json
import sys
from pathlib import Path

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
from tests import stubs  # noqa: E402


def _registry_payload() -> dict[str, object]:
    return {
        "name": "test-registry",
        "version": "1",
        "commands": [
            {"name": "demo:exec", "help": "Demo exec", "exec": "echo demo"},
        ],
        "taskTemplates": [],
        "plugins": {
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
        },
        "recipes": {},
        "recipe_configs": {},
    }


def test_register_plugin_commands_logs_events(monkeypatch, tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.json"
    payload = _registry_payload()
    registry_path.write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.setattr(plugin_loader, "REGISTRY_PATH", registry_path)
    monkeypatch.setattr(plugin_loader, "analytics_default", lambda: True)

    events: list[tuple[str, dict[str, object]]] = []

    def _record(name: str, payload: dict[str, object], *, enabled: bool = False) -> bool:
        events.append((name, payload))
        return enabled

    monkeypatch.setattr(plugin_loader, "record_event", _record)
    stubs.plugin_command.calls = []  # type: ignore[attr-defined]

    app = typer.Typer()
    plugin_loader.register_plugin_commands(app)

    commands = {(payload["plugin"], payload["command"]): payload for _, payload in events}
    assert ("registry", "demo:exec") in commands
    assert commands[("registry", "demo:exec")]["status"] == "registered"
    assert commands[("demo", "hello")]["status"] == "registered"


def test_load_registry_reports_schema_errors(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    registry_path = tmp_path / "registry.json"
    registry_path.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(plugin_loader, "REGISTRY_PATH", registry_path)
    monkeypatch.setattr(plugin_loader, "analytics_default", lambda: True)

    events: list[dict[str, object]] = []
    monkeypatch.setattr(
        plugin_loader,
        "record_event",
        lambda _name, payload, *, enabled=False: events.append(payload),
    )

    assert plugin_loader._load_registry(registry_path) is None
    captured = capsys.readouterr()
    assert "Invalid plug-in registry schema" in captured.err
    assert any(event.get("status") == "invalid" for event in events)


def test_load_registry_handles_missing_file(monkeypatch, tmp_path: Path, capsys) -> None:
    registry_path = tmp_path / "missing.json"

    monkeypatch.setattr(plugin_loader, "REGISTRY_PATH", registry_path)
    monkeypatch.setattr(plugin_loader, "analytics_default", lambda: True)

    events: list[dict[str, object]] = []
    monkeypatch.setattr(
        plugin_loader,
        "record_event",
        lambda _name, payload, *, enabled=False: events.append(payload),
    )

    assert plugin_loader._load_registry(registry_path) is None
    captured = capsys.readouterr()
    assert "Plug-in registry not found" in captured.err
    assert any(event.get("status") == "missing" for event in events)
