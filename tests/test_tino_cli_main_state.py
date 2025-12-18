import importlib
import json
import sys
import types
from pathlib import Path
from typing import Any

import pytest


# Ensure Typer is importable in isolation
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
from scripts.tino_cli.main import (  # noqa: E402
    API_URL_ENV,
    CLIState,
    app,
    build_state,
    compose_command,
    run_shell_command,
    show_whoami,
)

main_module = importlib.import_module("scripts.tino_cli.main")


@pytest.fixture()
def _test_state(tmp_path: Path) -> CLIState:
    return CLIState(
        dry_run=False,
        confirm=False,
        telemetry_enabled=False,
        log_path=tmp_path / "log.txt",
        identity={},
        services={},
    )


def test_build_state_populates_identity_and_services(monkeypatch, tmp_path: Path) -> None:
    called: dict[str, Any] = {}
    monkeypatch.setenv("TINO_CLI_LOG", str(tmp_path / "custom.log"))

    monkeypatch.setattr(main_module, "load_env_defaults", lambda: called.setdefault("load_env", True))
    monkeypatch.setattr(main_module, "snapshot_identity", lambda: {"USER": "alice"})
    monkeypatch.setattr(main_module, "analytics_default", lambda: True)

    class _Service:
        def __init__(self, value: str) -> None:
            self._value = value

        def resolve(self) -> str:
            return self._value

    monkeypatch.setattr(
        main_module,
        "_SERVICE_CONFIGS",
        (("svc", _Service("http://service")),),
    )

    state = build_state(dry_run=True, confirm=True)

    assert state.dry_run is True
    assert state.confirm is True
    assert state.telemetry_enabled is True
    assert state.identity == {"USER": "alice"}
    assert state.services == {"svc": "http://service"}
    assert state.log_path == tmp_path / "custom.log"
    assert called["load_env"] is True


def test_show_whoami_merges_identity_and_endpoints(monkeypatch, _test_state: CLIState) -> None:
    monkeypatch.setenv("USER", "env-user")
    monkeypatch.setenv("GROUP", "devs")
    monkeypatch.setenv("EMAIL", "me@example.com")
    monkeypatch.setenv(API_URL_ENV, "https://api.example.com")
    monkeypatch.setenv("EVENTS_URL", "https://events.example.com")

    monkeypatch.setattr(main_module, "load_env_defaults", lambda: None)

    state = _test_state
    state.telemetry_enabled = True
    state.confirm = True
    state.identity = {"SYSTEM_USER": "system"}
    state.services = {"svc": "https://svc"}

    whoami = show_whoami(state)

    assert whoami["confirm"] is True
    assert whoami["telemetry"] == {
        "enabled": True,
        "endpoint": "https://events.example.com",
    }
    assert whoami["log_path"].endswith("log.txt")
    assert whoami["endpoints"]["api"] == "https://api.example.com"
    assert whoami["identity"] == {
        "email": "me@example.com",
        "group": "devs",
        "SYSTEM_USER": "system",
        "user": "env-user",
    }
    assert whoami["services"] == {"svc": "https://svc"}


def test_run_shell_command_respects_dry_run(monkeypatch, capsys, _test_state: CLIState) -> None:
    state = _test_state
    state.dry_run = True

    result = run_shell_command(state, ["echo", "hello"])

    captured = capsys.readouterr()
    assert result == 0
    assert "[dry-run] echo hello" in captured.out


def test_run_shell_command_requires_confirmation(monkeypatch, capsys, _test_state: CLIState) -> None:
    state = _test_state
    confirm_message = "need --confirm"

    result = run_shell_command(state, ["echo", "hi"], require_confirm=True, confirm_message=confirm_message)

    captured = capsys.readouterr()
    assert result == 1
    assert confirm_message in captured.err


def test_run_shell_command_invokes_subprocess(monkeypatch, _test_state: CLIState) -> None:
    state = _test_state
    state.confirm = True
    calls: list[list[str]] = []
    monkeypatch.setattr(main_module.subprocess, "call", lambda cmd: calls.append(cmd) or 3)

    assert run_shell_command(state, ["doit"]) == 3
    assert calls == [["doit"]]


def test_compose_command_generates_tuple() -> None:
    assert compose_command("up", "-d") == (
        "docker",
        "compose",
        "-f",
        "docker-compose.yml",
        "up",
        "-d",
    )


def test_schedule_list_uses_shared_state(monkeypatch, _test_state: CLIState) -> None:
    responses: list[Any] = []
    monkeypatch.setattr(main_module, "_render_response", lambda payload: responses.append(payload))
    monkeypatch.setattr(main_module, "get_schedule", lambda state: {"state": state.confirm})

    ctx = types.SimpleNamespace(obj=_test_state)
    main_module.task_schedule_list(ctx)

    assert responses == [{"state": False}]


def test_schedule_update_enforces_confirm(monkeypatch, _test_state: CLIState) -> None:
    called: list[dict[str, Any]] = []
    monkeypatch.setattr(main_module, "update_schedule", lambda state, schedule: called.append({"state": state, "schedule": schedule}))

    ctx = types.SimpleNamespace(obj=_test_state)
    with pytest.raises(typer.Exit) as excinfo:
        main_module.task_schedule_update(ctx, schedule="{}")

    assert excinfo.value.exit_code == 1
    assert called == []


def test_schedule_update_dry_run_previews_payload(monkeypatch, capsys, _test_state: CLIState) -> None:
    _test_state.dry_run = True

    calls: list[dict[str, Any]] = []

    def _update(state, schedule):
        calls.append({"state": state.confirm, "schedule": schedule})
        return {"ok": True, "schedule": schedule}

    monkeypatch.setattr(main_module, "update_schedule", _update)

    ctx = types.SimpleNamespace(obj=_test_state)
    main_module.task_schedule_update(ctx, schedule="{\"foo\": 1}")

    captured = capsys.readouterr()
    assert calls == [{"state": False, "schedule": {"foo": 1}}]
    assert "[dry-run] Preview schedule update payload:" in captured.out
    rendered = captured.out.split("[dry-run] Preview schedule update payload:\n", 1)[1]
    decoder = json.JSONDecoder()
    payload, offset = decoder.raw_decode(rendered)
    response, _ = decoder.raw_decode(rendered[offset:].lstrip())
    assert payload == {"foo": 1}
    assert response == {"ok": True, "schedule": {"foo": 1}}
