"""Tests for legacy ``tino stack`` compatibility commands."""

from __future__ import annotations

import sys
import types

import pytest

_doctor_stub = types.ModuleType("scripts.tino_cli.doctor")
_doctor_stub.gather_report = lambda *args, **kwargs: None  # type: ignore[assignment]
_doctor_stub.gather_diagnostics = lambda *args, **kwargs: None  # type: ignore[assignment]
sys.modules.setdefault("scripts.tino_cli.doctor", _doctor_stub)

from scripts.tino_cli.main import app


@pytest.fixture()
def _capture_shell(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, object]]:
    """Capture ``run_shell_command`` invocations for assertions."""

    calls: list[dict[str, object]] = []

    def _fake_run_shell(
        state,
        command,
        *,
        require_confirm: bool = False,
        confirm_message: str = "Use --confirm to execute this command.",
    ) -> int:
        calls.append(
            {
                "command": tuple(command),
                "require_confirm": require_confirm,
                "confirm_message": confirm_message,
            }
        )
        return 0

    main_module = sys.modules["scripts.tino_cli.main"]
    monkeypatch.setattr(main_module, "run_shell_command", _fake_run_shell)
    return calls


def test_stack_down_full_invokes_compose_down(tino_cli_runner, _capture_shell) -> None:
    result = tino_cli_runner.invoke(app, ["--confirm", "stack", "down"])

    assert result.exit_code == 0
    assert _capture_shell == [
        {
            "command": ("docker", "compose", "-f", "docker-compose.yml", "down"),
            "require_confirm": True,
            "confirm_message": "Use --confirm to execute this command.",
        }
    ]


def test_stack_down_service_removes_compose_service(
    tino_cli_runner,
    _capture_shell,
) -> None:
    result = tino_cli_runner.invoke(app, ["--confirm", "stack", "down", "ume"])

    assert result.exit_code == 0
    assert _capture_shell == [
        {
            "command": (
                "docker",
                "compose",
                "-f",
                "docker-compose.yml",
                "rm",
                "-s",
                "-f",
                "ume",
            ),
            "require_confirm": True,
            "confirm_message": "Use --confirm to execute this command.",
        }
    ]
