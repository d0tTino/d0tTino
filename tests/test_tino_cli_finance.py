from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from scripts.tino_cli.clients import finance as finance_module
from scripts.tino_cli.main import app


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def _setup_cli_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parent.parent
    monkeypatch.chdir(project_root)
    monkeypatch.setenv("TINO_CLI_LOG", str(tmp_path / "tino-cli.log"))


def test_finance_snapshot_defaults(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, runner: CliRunner
) -> None:
    _setup_cli_env(monkeypatch, tmp_path)

    captured: dict[str, str | None] = {}

    def fake_snapshot(self, state, *, period: str, month: str | None = None):  # type: ignore[no-untyped-def]
        captured["period"] = period
        captured["month"] = month
        return {"period": period, "month": month}

    monkeypatch.setattr(finance_module.FinanceClient, "snapshot", fake_snapshot, raising=False)

    result = runner.invoke(app, ["--dry-run", "finance", "snapshot"])

    assert result.exit_code == 0
    assert captured == {"period": "monthly", "month": None}


def test_finance_snapshot_with_month(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, runner: CliRunner
) -> None:
    _setup_cli_env(monkeypatch, tmp_path)

    captured: dict[str, str | None] = {}

    def fake_snapshot(self, state, *, period: str, month: str | None = None):  # type: ignore[no-untyped-def]
        captured["period"] = period
        captured["month"] = month
        return {"period": period, "month": month}

    monkeypatch.setattr(finance_module.FinanceClient, "snapshot", fake_snapshot, raising=False)

    result = runner.invoke(
        app,
        ["--dry-run", "finance", "snapshot", "--month", "2024-01"],
    )

    assert result.exit_code == 0
    assert captured == {"period": "monthly", "month": "2024-01"}
