from __future__ import annotations

import json

import pytest
import importlib

from typer.testing import CliRunner

from scripts.tino_cli import doctor
from scripts.tino_cli.doctor import DoctorCheck, DoctorReport
from scripts.tino_cli.main import app


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def _stub_check(name: str, ok: bool, details: dict[str, object] | None = None) -> DoctorCheck:
    message = "ok" if ok else "error"
    return DoctorCheck(name=name, ok=ok, message=message, details=details)


def test_doctor_report_success(monkeypatch: pytest.MonkeyPatch) -> None:
    docker_check = _stub_check("docker", True, {"server_version": "25.0"})
    ports_check = _stub_check("ports", True, {"occupied": []})
    hooks_check = _stub_check("git-hooks", True, {"path": ".githooks"})

    monkeypatch.setattr(doctor, "_check_docker_engine", lambda: docker_check)
    monkeypatch.setattr(doctor, "_check_required_ports", lambda: ports_check)
    monkeypatch.setattr(doctor, "_check_git_hooks", lambda: hooks_check)

    report = doctor.gather_report()
    assert report.ok is True

    payload = report.to_dict()
    assert payload["summary"] == {"ok": True, "total": 3, "passed": 3, "failed": 0}

    docker_payload = next(item for item in payload["checks"] if item["name"] == "docker")
    assert docker_payload["details"]["server_version"] == "25.0"


def test_doctor_report_with_port_conflicts(monkeypatch: pytest.MonkeyPatch) -> None:
    docker_check = _stub_check("docker", True, {"server_version": "25.0"})
    ports_check = _stub_check("ports", False, {"occupied": [4222, 8080]})
    hooks_check = _stub_check("git-hooks", True, {"path": ".githooks"})

    monkeypatch.setattr(doctor, "_check_docker_engine", lambda: docker_check)
    monkeypatch.setattr(doctor, "_check_required_ports", lambda: ports_check)
    monkeypatch.setattr(doctor, "_check_git_hooks", lambda: hooks_check)

    report = doctor.gather_report()
    assert report.ok is False

    payload = report.to_dict()
    assert payload["summary"]["failed"] == 1

    port_payload = next(item for item in payload["checks"] if item["name"] == "ports")
    assert port_payload["details"]["occupied"] == [4222, 8080]


def test_cli_doctor_outputs_report(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    report = DoctorReport(
        [
            _stub_check("docker", True, {"server_version": "25.0"}),
            _stub_check("ports", False, {"occupied": [4222]}),
            _stub_check("git-hooks", True, {"path": ".githooks"}),
        ]
    )

    monkeypatch.setattr(doctor, "gather_report", lambda skip_checks=False: report)
    main_module = importlib.import_module("scripts.tino_cli.main")
    monkeypatch.setattr(main_module, "gather_report", lambda skip_checks=False: report)

    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1

    payload = json.loads(result.stdout)
    assert payload["summary"]["failed"] == 1
    assert any(item["name"] == "ports" for item in payload["checks"])
