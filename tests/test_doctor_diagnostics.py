from __future__ import annotations

import pytest

from scripts.tino_cli import doctor


class _DummyConnection:
    def __enter__(self):  # pragma: no cover - simple helper
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def test_service_endpoints_reports_reachability(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, int]] = []

    def fake_connection(addr: tuple[str, int], timeout: float) -> _DummyConnection:
        host, port = addr
        calls.append((host, port))
        if port == 8080:
            return _DummyConnection()
        raise OSError("unreachable")

    monkeypatch.setattr(doctor.socket, "create_connection", fake_connection)

    payload = doctor._service_endpoints(
        {"ok": "http://localhost:8080", "bad": "http://example.com:9090"}, dry_run=False
    )

    assert payload["status"] == doctor._STATUS_WARNING
    assert payload["reachable"] == 1
    assert payload["total"] == 2
    assert calls == [("localhost", 8080), ("example.com", 9090)]

    ok_item = next(item for item in payload["items"] if item["name"] == "ok")
    bad_item = next(item for item in payload["items"] if item["name"] == "bad")
    assert ok_item["status"] == doctor._STATUS_OK
    assert ok_item["reachable"] is True
    assert bad_item["status"] == doctor._STATUS_WARNING
    assert bad_item["error"] == "unreachable"


def test_service_endpoints_dry_run_is_skipped() -> None:
    payload = doctor._service_endpoints({"svc": "https://example.com"}, dry_run=True)
    assert payload["status"] == doctor._STATUS_SKIPPED
    assert payload["items"][0]["reachable"] is None
    assert payload["items"][0]["status"] == doctor._STATUS_SKIPPED


def test_env_tokens_check_reports_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(doctor, "_collect_env_keys", lambda: ("API_TOKEN", "USER_PASSWORD"))
    monkeypatch.setenv("API_TOKEN", "secret")
    monkeypatch.delenv("USER_PASSWORD", raising=False)

    payload = doctor._env_tokens_check()

    assert payload["status"] == doctor._STATUS_WARNING
    assert payload["missing"] == ["USER_PASSWORD"]
    assert payload["items"] == [
        {"name": "API_TOKEN", "present": True},
        {"name": "USER_PASSWORD", "present": False},
    ]


def test_summarise_counts_errors_and_warnings() -> None:
    summary = doctor._summarise(
        {
            "docker": {"status": doctor._STATUS_OK},
            "services": {"status": doctor._STATUS_WARNING},
            "env": {"status": doctor._STATUS_ERROR},
        }
    )

    assert summary.status == doctor._STATUS_ERROR
    assert summary.errors == 1
    assert summary.warnings == 1
