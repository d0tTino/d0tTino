"""Tests for cockpit context injection handling."""

from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path

import pytest

from importlib import import_module

from scripts.tino_cli import actions
from scripts.tino_cli.models import TelemetryStatus


main_module = import_module("scripts.tino_cli.main")


class _Result:
    payload = {"ok": True}


@pytest.fixture()
def _patched_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr(actions, "ensure_cache_dir", lambda: tmp_path)
    monkeypatch.setattr(
        actions,
        "build_state",
        lambda *, dry_run, confirm: SimpleNamespace(dry_run=dry_run, confirm=confirm),
    )
    monkeypatch.setattr(actions, "telemetry_status", lambda: TelemetryStatus(enabled=False))


def test_cockpit_inject_context_parses_combined_payload(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, _patched_environment
) -> None:
    recorded: dict[str, object] = {}

    def _fake_signal(self, state, task_id, *, signal, link=None, note=None):  # noqa: ANN001
        recorded.update({
            "task_id": task_id,
            "signal": signal,
            "link": link,
            "note": note,
        })
        return _Result()

    monkeypatch.setattr(main_module.TaskCascadenceClient, "signal", _fake_signal, raising=False)

    result = actions.run_action(
        "cockpit-inject-context",
        payload="job-42::add more details",
        confirm=False,
    )

    assert recorded == {
        "task_id": "job-42",
        "signal": "context",
        "link": None,
        "note": "add more details",
    }
    assert "--note" in result.details["commands"][0]


def test_cockpit_inject_context_uses_link_for_urls(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, _patched_environment
) -> None:
    recorded: dict[str, object] = {}

    def _fake_signal(self, state, task_id, *, signal, link=None, note=None):  # noqa: ANN001
        recorded.update({
            "task_id": task_id,
            "signal": signal,
            "link": link,
            "note": note,
        })
        return _Result()

    monkeypatch.setattr(main_module.TaskCascadenceClient, "signal", _fake_signal, raising=False)

    result = actions.run_action(
        "cockpit-inject-context",
        payload="https://example.com/context",
        confirm=False,
        job_id="job-42",
    )

    assert recorded == {
        "task_id": "job-42",
        "signal": "context",
        "link": "https://example.com/context",
        "note": None,
    }
    assert "--link" in result.details["commands"][0]


def test_cockpit_inject_context_requires_job(
    tmp_path: Path, _patched_environment
) -> None:
    result = actions.run_action(
        "cockpit-inject-context",
        payload="just some context",
        confirm=False,
    )

    assert result.details["exit_code"] == 1
    assert result.details["error"] == "Task identifier required for context injection."
