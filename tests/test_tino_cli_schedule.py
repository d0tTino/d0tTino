"""CLI coverage for ``tino task schedule`` commands."""
from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

tino_cli_main = importlib.import_module("scripts.tino_cli.main")
app = tino_cli_main.app


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def _setup_cli_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parent.parent
    monkeypatch.chdir(project_root)
    monkeypatch.setenv("TINO_CLI_LOG", str(tmp_path / "tino-cli.log"))


def test_task_schedule_list_uses_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, runner: CliRunner) -> None:
    _setup_cli_env(monkeypatch, tmp_path)

    captured: dict[str, object] = {}

    def fake_get_schedule(state):  # type: ignore[no-untyped-def]
        captured["state"] = state
        return {"items": ["alpha"]}

    monkeypatch.setattr(tino_cli_main, "get_schedule", fake_get_schedule)

    result = runner.invoke(app, ["task", "schedule", "list"])

    assert result.exit_code == 0
    assert json.loads(result.output) == {"items": ["alpha"]}
    assert "state" in captured


def test_task_schedule_update_requires_confirm(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    runner: CliRunner,
) -> None:
    _setup_cli_env(monkeypatch, tmp_path)

    called: dict[str, object] = {}

    def fake_update_schedule(state, *, schedule):  # type: ignore[no-untyped-def]
        called["schedule"] = schedule
        return {"ok": True}

    monkeypatch.setattr(tino_cli_main, "update_schedule", fake_update_schedule)

    result = runner.invoke(
        app,
        ["task", "schedule", "update", "--schedule", json.dumps({"timezone": "UTC"})],
    )

    assert result.exit_code == 1
    assert "Use --confirm" in result.output
    assert called == {}


def test_task_schedule_update_dry_run_preview(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    runner: CliRunner,
) -> None:
    _setup_cli_env(monkeypatch, tmp_path)

    captured: dict[str, object] = {}

    def fake_update_schedule(state, *, schedule):  # type: ignore[no-untyped-def]
        captured["dry_run"] = state.dry_run
        captured["schedule"] = schedule
        return None

    monkeypatch.setattr(tino_cli_main, "update_schedule", fake_update_schedule)

    payload = {"timezone": "UTC", "windows": ["nightly"]}
    result = runner.invoke(
        app,
        ["--dry-run", "task", "schedule", "update", "--schedule", json.dumps(payload)],
    )

    assert result.exit_code == 0
    assert "[dry-run] Preview schedule update payload" in result.output
    assert json.dumps(payload, indent=2) in result.output
    assert captured == {"dry_run": True, "schedule": payload}


def test_task_schedule_update_executes_with_confirm(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    runner: CliRunner,
) -> None:
    _setup_cli_env(monkeypatch, tmp_path)

    captured: dict[str, object] = {}

    def fake_update_schedule(state, *, schedule):  # type: ignore[no-untyped-def]
        captured["confirm"] = state.confirm
        captured["schedule"] = schedule
        return {"ok": True}

    monkeypatch.setattr(tino_cli_main, "update_schedule", fake_update_schedule)

    payload = {"timezone": "UTC"}
    result = runner.invoke(
        app,
        ["--confirm", "task", "schedule", "update", "--schedule", json.dumps(payload)],
    )

    assert result.exit_code == 0
    assert json.loads(result.output) == {"ok": True}
    assert captured == {"confirm": True, "schedule": payload}
