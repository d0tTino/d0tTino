"""Integration tests for the Typer-powered ``tino`` CLI services."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from scripts.tino_cli.main import app

if TYPE_CHECKING:
    from typer.testing import CliRunner


@pytest.fixture(autouse=True)
def _set_repo_root(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure CLI invocations run from the repository root."""

    repo_root = Path(__file__).resolve().parent.parent
    monkeypatch.chdir(repo_root)


def _enable_telemetry(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, dict, bool]]:
    recorded: list[tuple[str, dict, bool]] = []

    def _capture(name: str, payload: dict, *, enabled: bool = True) -> bool:
        recorded.append((name, payload, enabled))
        return True

    import importlib

    module = importlib.import_module("scripts.tino_cli.main")
    monkeypatch.setattr(module, "analytics_default", lambda: True)
    monkeypatch.setattr("scripts.tino_cli.clients.base.record_event", _capture)
    return recorded


def test_task_run_dry_run_sets_telemetry_flag(
    tino_cli_runner: "CliRunner",
    fake_http_service: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded = _enable_telemetry(monkeypatch)

    result = tino_cli_runner.invoke(
        app,
        ["--dry-run", "task", "run", "demo", "--payload", json.dumps({"foo": "bar"})],
    )

    assert result.exit_code == 0
    assert "[dry-run]" in result.output
    assert recorded
    name, payload, enabled = recorded[0]
    assert name.endswith("taskcascadence.run")
    assert payload.get("dry_run") is True
    assert enabled is True
    # When running in dry-run mode the HTTP layer should not be invoked.
    assert fake_http_service["calls"] == []


def test_task_run_invokes_remote_service(
    tino_cli_runner: "CliRunner",
    fake_http_service: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded = _enable_telemetry(monkeypatch)
    fake_http_service["stub"](
        "post",
        "/tasks/run",
        {"status": "queued", "task": "demo"},
    )

    result = tino_cli_runner.invoke(
        app,
        ["task", "run", "demo", "--payload", json.dumps({"foo": 42})],
    )

    assert result.exit_code == 0
    assert json.loads(result.output) == {"status": "queued", "task": "demo"}

    call = fake_http_service["calls"][0]
    assert call["method"] == "post"
    assert call["url"].endswith("/tasks/run")
    assert call["json_payload"] == {"task": "demo", "payload": {"foo": 42}}

    assert recorded
    _, payload, enabled = recorded[0]
    assert payload["status"] == 200
    assert payload["url"].endswith("/tasks/run")
    assert enabled is True


def test_task_signal_requires_confirmation(
    tino_cli_runner: "CliRunner",
    fake_http_service: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_telemetry(monkeypatch)

    result = tino_cli_runner.invoke(app, ["task", "signal", "abc123", "--signal", "cancel"])

    assert result.exit_code == 1
    assert "Use --confirm" in result.output
    assert fake_http_service["calls"] == []


def test_task_signal_with_confirmation_hits_api(
    tino_cli_runner: "CliRunner",
    fake_http_service: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded = _enable_telemetry(monkeypatch)
    fake_http_service["stub"]("post", "/tasks/abc123/signal", {"ok": True})

    result = tino_cli_runner.invoke(
        app,
        [
            "--confirm",
            "task",
            "signal",
            "abc123",
            "--signal",
            "cancel",
            "--link",
            "https://example.com",
            "--note",
            "Investigate",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.output) == {"ok": True}
    call = fake_http_service["calls"][0]
    assert call["url"].endswith("/tasks/abc123/signal")
    assert call["json_payload"] == {
        "signal": "cancel",
        "link": "https://example.com",
        "note": "Investigate",
    }
    assert any(evt[0].endswith("signal") for evt in recorded)


def test_docs_publish_uses_configured_endpoint(
    tino_cli_runner: "CliRunner",
    fake_http_service: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded = _enable_telemetry(monkeypatch)
    fake_http_service["stub"]("post", "/docs/publish", {"site": "handbook"})

    result = tino_cli_runner.invoke(
        app,
        ["docs", "publish", "handbook", "--site", "handbook", "--version", "v1"],
    )

    assert result.exit_code == 0
    assert json.loads(result.output) == {"site": "handbook"}
    call = fake_http_service["calls"][0]
    assert call["json_payload"] == {
        "target": "handbook",
        "doc_id": "handbook",
        "site": "handbook",
        "version": "v1",
    }
    assert recorded
    assert recorded[0][1]["status"] == 200


def test_logs_requires_confirmation(
    tino_cli_runner: "CliRunner",
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = tino_cli_runner.invoke(app, ["logs", "ume"])
    assert result.exit_code == 1
    assert "Use --confirm" in result.output


def test_logs_dry_run_skips_subprocess(
    tino_cli_runner: "CliRunner",
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: list[list[str]] = []

    def _fake_call(cmd):
        called.append(cmd)
        return 0

    monkeypatch.setattr("subprocess.call", _fake_call)
    result = tino_cli_runner.invoke(app, ["--dry-run", "logs", "ume"])
    assert result.exit_code == 0
    assert "[dry-run]" in result.output
    assert called == []


def test_logs_confirm_invokes_subprocess(
    tino_cli_runner: "CliRunner",
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[list[str]] = []

    def _fake_call(cmd):
        captured.append(cmd)
        return 0

    monkeypatch.setattr("subprocess.call", _fake_call)

    result = tino_cli_runner.invoke(app, ["--confirm", "logs", "ume"])

    assert result.exit_code == 0
    assert captured
    assert captured[0][:4] == ["docker", "compose", "-f", "docker-compose.yml"]
    assert captured[0][-1] == "ume"


