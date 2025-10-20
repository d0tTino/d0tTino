from __future__ import annotations

import json
from pathlib import Path

import pytest
import typer.main
import click
import typing
import types
from typer.testing import CliRunner

from scripts.tino_cli import plugin_loader
from scripts.tino_cli.main import app


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(autouse=True)
def _typer_optional_support(monkeypatch: pytest.MonkeyPatch) -> None:
    original = typer.main.get_click_type

    def _patched(*, annotation, parameter_info):  # type: ignore[override]
        if isinstance(annotation, types.UnionType):
            args = typing.get_args(annotation)
            if all(arg in {str, type(None)} for arg in args):
                return click.STRING
        if isinstance(annotation, str):
            normalized = annotation.replace(" ", "").replace("typing.", "")
            normalized = normalized.replace("NoneType", "None")
            parts = normalized.split("|")
            if all(part in {"str", "None"} for part in parts):
                return click.STRING
            if any(part in {"list[str]", "List[str]"} for part in parts):
                return click.STRING
        return original(annotation=annotation, parameter_info=parameter_info)

    monkeypatch.setattr(typer.main, "get_click_type", _patched)


def test_help_lists_plugins(runner: CliRunner) -> None:
    commands = {command.plugin for command in plugin_loader.iter_plugin_commands()}
    assert "sample" in commands


def test_bootstrap_whoami_dry_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    log_path = tmp_path / "tino-cli.log"
    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    monkeypatch.setenv("TINO_CLI_LOG", str(log_path))
    result = runner.invoke(app, ["--dry-run", "bootstrap", "whoami"])
    assert result.exit_code == 0
    assert "[dry-run]" in result.output


def test_whoami_reports_identity_and_services(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, runner: CliRunner
) -> None:
    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    monkeypatch.setenv("TINO_CLI_LOG", str(tmp_path / "cli.log"))
    monkeypatch.setenv("USER", "cli-tester")
    monkeypatch.setenv("HOSTNAME", "cli-host")
    monkeypatch.setenv("TASKCASCADENCE_URL", "http://example.local/tasks")
    monkeypatch.setenv("STORM_URL", "http://example.local/storm")
    monkeypatch.setenv("UME_URL", "http://example.local/ume")
    monkeypatch.setenv("FINANCE_URL", "http://example.local/finance")
    monkeypatch.setenv("DOCS_URL", "http://example.local/docs")

    result = runner.invoke(app, ["whoami"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["identity"]["USER"] == "cli-tester"
    assert data["identity"]["HOSTNAME"] == "cli-host"
    assert data["services"] == {
        "docs": "http://example.local/docs",
        "finance": "http://example.local/finance",
        "storm": "http://example.local/storm",
        "taskcascadence": "http://example.local/tasks",
        "ume": "http://example.local/ume",
    }


def test_wishlist_add_dry_run(monkeypatch: pytest.MonkeyPatch, runner: CliRunner, tmp_path: Path) -> None:
    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    monkeypatch.setenv("TINO_CLI_LOG", str(tmp_path / "log"))
    result = runner.invoke(app, ["--dry-run", "wishlist", "add", "Test item"])
    assert result.exit_code == 0
    assert "Test item" in result.output


def test_task_run_dry_run(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    result = runner.invoke(app, ["--dry-run", "task", "run", "demo", "--payload", json.dumps({"foo": "bar"})])
    assert result.exit_code == 0
    assert "[dry-run] POST" in result.output


def test_whoami_identity(monkeypatch: pytest.MonkeyPatch, runner: CliRunner, tmp_path: Path) -> None:
    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    log_path = tmp_path / "whoami.log"
    monkeypatch.setenv("TINO_CLI_LOG", str(log_path))
    monkeypatch.setenv("USER", "cli-user")
    monkeypatch.setenv("GROUP", "cli-group")
    monkeypatch.setenv("EMAIL", "cli-user@example.test")
    monkeypatch.setenv("EVENTS_ENABLED", "1")
    monkeypatch.setenv("EVENTS_URL", "https://events.example.test")
    monkeypatch.setenv("TINO_API_URL", "https://api.example.test")
    monkeypatch.setenv("TASKCASCADENCE_URL", "https://tasks.example.test")
    monkeypatch.setenv("STORM_URL", "https://storm.example.test")
    monkeypatch.setenv("UME_URL", "https://ume.example.test")
    monkeypatch.setenv("FINANCE_URL", "https://finance.example.test")
    monkeypatch.setenv("DOCS_URL", "https://docs.example.test")

    result = runner.invoke(app, ["whoami"])
    assert result.exit_code == 0

    payload = json.loads(result.output)
    identity = payload.get("identity") or {}
    assert identity.get("user") == "cli-user"
    assert identity.get("group") == "cli-group"
    assert identity.get("email") == "cli-user@example.test"

    endpoints = payload.get("endpoints") or {}
    assert endpoints.get("api") == "https://api.example.test"
    assert endpoints.get("taskcascadence") == "https://tasks.example.test"
    assert endpoints.get("storm") == "https://storm.example.test"
    assert endpoints.get("ume") == "https://ume.example.test"
    assert endpoints.get("finance") == "https://finance.example.test"
    assert endpoints.get("docs") == "https://docs.example.test"

    telemetry = payload.get("telemetry") or {}
    assert telemetry.get("enabled") is True
    assert telemetry.get("endpoint") == "https://events.example.test"
    assert payload.get("log_path") == str(log_path)
