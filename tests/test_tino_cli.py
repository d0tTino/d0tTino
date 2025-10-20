from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from scripts.tino_cli import plugin_loader
from scripts.tino_cli.main import app


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


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
