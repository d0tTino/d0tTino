import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple
from urllib.parse import urlparse

import pytest
import requests

_site_packages = (
    Path(sys.executable).resolve().parent.parent
    / "lib"
    / f"python{sys.version_info.major}.{sys.version_info.minor}"
    / "site-packages"
)
_typer_init = _site_packages / "typer" / "__init__.py"
_typer_spec = importlib.util.spec_from_file_location("typer", _typer_init)
if _typer_spec and _typer_spec.loader:
    sys.modules.pop("typer", None)
    for _name in list(sys.modules):
        if _name.startswith("typer."):
            sys.modules.pop(_name, None)
    _typer_module = importlib.util.module_from_spec(_typer_spec)
    _typer_module.__path__ = [str(_typer_init.parent)]
    sys.modules["typer"] = _typer_module
    _typer_spec.loader.exec_module(_typer_module)

from typer.testing import CliRunner  # noqa: E402

if importlib.util.find_spec("llm") is None:
    # Ensure the repository root is on sys.path when running tests directly
    repo_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo_root))
    if importlib.util.find_spec("llm") is None:
        raise ImportError(
            "The 'llm' package could not be imported. Install this repository with 'pip install -e .' before running tests."
        )


def pytest_configure(config):
    """Normalize cached node IDs across operating systems."""
    if os.name == "nt":
        return
    try:
        nodeids = config.cache.get("cache/nodeids", [])
    except NotImplementedError:
        config.cache.set("cache/nodeids", [])
        return

    normalized = []
    changed = False
    for nid in nodeids:
        if hasattr(nid, "as_posix"):
            normalized.append(nid.as_posix())
            changed = True
        else:
            normalized.append(str(nid))

    if changed:
        config.cache.set("cache/nodeids", normalized)


@pytest.fixture()
def tino_cli_runner() -> CliRunner:
    """Return a ``CliRunner`` configured for ``tino`` CLI tests."""

    return CliRunner()


@pytest.fixture()
def fake_http_service(monkeypatch: pytest.MonkeyPatch) -> Dict[str, Any]:
    """Intercept HTTP calls performed by ``BaseClient`` implementations.

    The fixture captures each request issued via ``requests.Session`` and
    provides ``stub`` helpers for returning canned JSON payloads. Streaming
    responses are represented by lists of UTF-8 encoded lines.
    """

    calls: list[Dict[str, Any]] = []
    stubs: Dict[Tuple[str, str, bool], Tuple[Any, int]] = {}

    def _resolve(method: str, url: str, *, stream: bool = False, **kwargs: Any) -> Tuple[Any, int]:
        parsed = urlparse(url)
        key = (method.lower(), parsed.path or "", stream)
        payload, status = stubs.get(key, ({"echo": {"method": method.lower(), "path": parsed.path, **kwargs}}, 200))
        return payload, status

    class _Response:
        def __init__(self, url: str, payload: Any, status: int = 200) -> None:
            self._payload = payload
            self.status_code = status
            self.url = url
            self.text = json.dumps(payload)

        def json(self) -> Any:
            return self._payload

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise requests.HTTPError(f"status {self.status_code} for {self.url}")

    class _StreamResponse(_Response):
        def __enter__(self) -> "_StreamResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:  # type: ignore[override]
            return False

        def iter_lines(self) -> Iterable[bytes]:
            lines: Iterable[str]
            payload = self._payload
            if isinstance(payload, dict):
                lines = payload.get("lines", [])  # type: ignore[assignment]
            else:
                lines = payload
            for line in lines:
                yield str(line).encode("utf-8")

    def _request(self, method: str, url: str, **kwargs: Any):
        payload, status = _resolve(method, url, **kwargs)
        entry: Dict[str, Any] = {"method": method.lower(), "url": url, "status": status}
        if "json" in kwargs:
            entry["json_payload"] = kwargs["json"]
        if "params" in kwargs:
            entry["params"] = kwargs["params"]
        calls.append(entry)
        return _Response(url, payload, status)

    def _get(self, url: str, *, stream: bool = False, **kwargs: Any):
        payload, status = _resolve("get", url, stream=stream, **kwargs)
        entry: Dict[str, Any] = {"method": "get", "url": url, "stream": stream, "status": status}
        if "params" in kwargs:
            entry["params"] = kwargs["params"]
        calls.append(entry)
        return _StreamResponse(url, payload, status)

    def _stub(method: str, path: str, payload: Any, *, status: int = 200, stream: bool = False) -> None:
        stubs[(method.lower(), path, stream)] = (payload, status)

    monkeypatch.setattr(requests.Session, "request", _request, raising=False)
    monkeypatch.setattr(requests.Session, "get", _get, raising=False)

    return {"calls": calls, "stub": _stub}
