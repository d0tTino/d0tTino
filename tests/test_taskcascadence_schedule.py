"""Unit tests for TaskCascadence schedule helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import sys
import types

import pytest

_stub_run = types.ModuleType("scripts.tino_cli.run")
_stub_run.main = lambda *args, **kwargs: None  # type: ignore[assignment]
sys.modules.setdefault("scripts.tino_cli.run", _stub_run)

from scripts.tino_cli.clients.taskcascadence import TaskCascadenceClient  # noqa: E402
from scripts.tino_cli.state import CLIState  # noqa: E402


def _build_state(tmp_path: Path, *, dry_run: bool, telemetry_enabled: bool) -> CLIState:
    return CLIState(
        dry_run=dry_run,
        confirm=True,
        telemetry_enabled=telemetry_enabled,
        log_path=tmp_path / "cli.log",
    )


def _capture_events(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, dict[str, Any], bool]]:
    events: list[tuple[str, dict[str, Any], bool]] = []

    def _record(name: str, payload: dict[str, Any], *, enabled: bool = False) -> bool:  # noqa: FBT002
        events.append((name, payload, enabled))
        return True

    monkeypatch.setattr("scripts.tino_cli.clients.base.record_event", _record)
    return events


def test_get_schedule_success(fake_http_service: dict, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_http_service["stub"]("get", "/schedule", {"items": []})
    events = _capture_events(monkeypatch)

    state = _build_state(tmp_path, dry_run=False, telemetry_enabled=True)
    client = TaskCascadenceClient()

    result = client.get_schedule(state)

    assert result is not None
    assert result.payload == {"items": []}
    assert fake_http_service["calls"][0]["method"] == "get"
    assert fake_http_service["calls"][0]["url"].endswith("/schedule")

    assert len(events) == 1
    name, payload, enabled = events[0]
    assert name == "tino_cli.taskcascadence.get_schedule"
    assert enabled is True
    assert payload["action"] == "get_schedule"
    assert payload["url"].endswith("/schedule")
    assert payload["status"] == 200
    assert "duration_ms" in payload


def test_update_schedule_success(fake_http_service: dict, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_http_service["stub"]("patch", "/schedule", {"ok": True})
    events = _capture_events(monkeypatch)

    state = _build_state(tmp_path, dry_run=False, telemetry_enabled=True)
    client = TaskCascadenceClient()

    result = client.update_schedule(state, schedule={"timezone": "UTC"})

    assert result is not None
    assert result.payload == {"ok": True}

    assert fake_http_service["calls"][0]["method"] == "patch"
    assert fake_http_service["calls"][0]["url"].endswith("/schedule")
    assert fake_http_service["calls"][0]["json_payload"] == {"timezone": "UTC"}

    assert len(events) == 1
    name, payload, enabled = events[0]
    assert name == "tino_cli.taskcascadence.update_schedule"
    assert enabled is True
    assert payload["action"] == "update_schedule"
    assert payload["url"].endswith("/schedule")
    assert payload["status"] == 200
    assert "duration_ms" in payload


def test_update_schedule_dry_run(fake_http_service: dict, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    events = _capture_events(monkeypatch)

    state = _build_state(tmp_path, dry_run=True, telemetry_enabled=True)
    client = TaskCascadenceClient()

    result = client.update_schedule(state, schedule={"timezone": "UTC"})

    assert result is None
    assert fake_http_service["calls"] == []

    captured = capsys.readouterr()
    assert "[dry-run] PATCH http://127.0.0.1:6001/schedule" in captured.out

    assert len(events) == 1
    name, payload, enabled = events[0]
    assert name == "tino_cli.taskcascadence.update_schedule"
    assert enabled is True
    assert payload["action"] == "update_schedule"
    assert payload["url"].endswith("/schedule")
    assert payload["dry_run"] is True
    assert payload["status"] is None
