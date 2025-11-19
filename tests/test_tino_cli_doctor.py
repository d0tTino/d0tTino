from __future__ import annotations

import json
from pathlib import Path

import importlib

import pytest

from scripts.tino_cli import doctor
from scripts.tino_cli.main import run_doctor
from scripts.tino_cli.state import CLIState


def _make_state(*, dry_run: bool = False) -> CLIState:
    return CLIState(
        dry_run=dry_run,
        confirm=not dry_run,
        telemetry_enabled=False,
        log_path=Path("cli.log"),
        identity={},
        services={"docs": "http://example.invalid"},
    )


def test_gather_diagnostics_reports_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    docker_payload = {"status": "ok", "message": "docker ok"}
    services_payload = {"status": "warning", "items": [{"name": "docs"}]}
    tokens_payload = {"status": "error", "missing": ["TOKEN"]}
    hooks_payload = {"status": "ok", "message": "hooks"}

    monkeypatch.setattr(doctor, "_docker_check", lambda: docker_payload)
    monkeypatch.setattr(
        doctor,
        "_service_endpoints",
        lambda services, dry_run: services_payload,
    )
    monkeypatch.setattr(doctor, "_env_tokens_check", lambda: tokens_payload)
    monkeypatch.setattr(doctor, "_git_hooks_check", lambda: hooks_payload)

    report = doctor.gather_diagnostics(_make_state())

    assert report["summary"] == {"status": "error", "errors": 1, "warnings": 1}
    assert report["checks"] == {
        "docker": docker_payload,
        "services": services_payload,
        "env_tokens": tokens_payload,
        "git_hooks": hooks_payload,
    }


def test_run_doctor_dry_run_reports_flag(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    diagnostics = {
        "dry_run": True,
        "confirm": False,
        "summary": {"status": "ok", "errors": 0, "warnings": 0},
        "checks": {"docker": {"status": "ok"}},
    }

    monkeypatch.setattr(doctor, "gather_diagnostics", lambda state: dict(diagnostics))
    main_module = importlib.import_module("scripts.tino_cli.main")
    monkeypatch.setattr(main_module, "gather_diagnostics", lambda state: dict(diagnostics))

    code = run_doctor(_make_state(dry_run=True))

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["dry_run"] is True
    assert payload["summary"]["dry_run"] is True
    assert payload["checks"]["docker"] == {"status": "ok"}
