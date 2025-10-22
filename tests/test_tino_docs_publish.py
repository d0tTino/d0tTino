from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

if "scripts.tino_cli.doctor" not in sys.modules:
    _doctor_stub = ModuleType("scripts.tino_cli.doctor")

    class _Report:
        def to_dict(self) -> dict[str, object]:
            return {}

    _doctor_stub.gather_report = lambda skip_checks=False: _Report()
    _doctor_stub.gather_diagnostics = lambda: []
    sys.modules["scripts.tino_cli.doctor"] = _doctor_stub

from scripts.tino_cli.clients.docs import DocsClient
from scripts.tino_cli.main import app


@pytest.fixture()
def _docs_stub(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, object]]:
    """Install a stubbed ``DocsClient.request`` implementation for tests."""

    calls: list[dict[str, object]] = []

    def _fake_request(
        self,
        state,  # noqa: ANN001 - ``CLIState`` at runtime
        method: str,
        path: str,
        *,
        json_payload: dict[str, object] | None = None,
        **kwargs,
    ) -> SimpleNamespace:
        entry = {"method": method, "path": path, "json_payload": json_payload}
        calls.append(entry)
        return SimpleNamespace(payload={"echo": json_payload})

    monkeypatch.setattr(DocsClient, "request", _fake_request, raising=False)
    return calls


def test_docs_publish_uses_file_path(
    tino_cli_runner: "CliRunner",
    _docs_stub: list[dict[str, object]],
    tmp_path: Path,
) -> None:
    doc_path = tmp_path / "site.json"
    doc_path.write_text("{}", encoding="utf-8")

    result = tino_cli_runner.invoke(app, ["docs", "publish", str(doc_path)])

    assert result.exit_code == 0

    payload = json.loads(result.output)
    expected = {"target": str(doc_path), "path": str(doc_path)}
    assert payload == {"echo": expected}

    assert len(_docs_stub) == 1
    assert _docs_stub[0]["json_payload"] == expected


def test_docs_publish_defaults_to_env_target(
    tino_cli_runner: "CliRunner",
    monkeypatch: pytest.MonkeyPatch,
    _docs_stub: list[dict[str, object]],
) -> None:
    monkeypatch.setenv("TINO_DOC_TARGET", "handbook/latest")

    result = tino_cli_runner.invoke(app, ["docs", "publish"])

    assert result.exit_code == 0

    payload = json.loads(result.output)
    expected = {"target": "handbook/latest", "doc_id": "handbook/latest"}
    assert payload == {"echo": expected}

    assert len(_docs_stub) == 1
    assert _docs_stub[0]["json_payload"] == expected
