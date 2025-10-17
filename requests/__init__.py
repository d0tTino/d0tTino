"""Minimal requests compatibility shim for tests."""
from __future__ import annotations

import json as _json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional

__all__ = [
    "HTTPError",
    "RequestException",
    "Response",
    "get",
    "post",
    "request",
]


class RequestException(Exception):
    """Base exception for the shim."""


class HTTPError(RequestException):
    """Raised when a response indicates failure."""

    def __init__(self, response: "Response") -> None:
        self.response = response
        super().__init__(f"{response.status_code} {response.reason}")


@dataclass
class Response:
    """Lightweight response wrapper resembling :mod:`requests`."""

    _body: bytes
    status_code: int
    headers: MutableMapping[str, str]
    reason: str = ""

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 400

    @property
    def text(self) -> str:
        return self._body.decode("utf-8", errors="replace")

    def json(self) -> Any:
        return _json.loads(self.text or "null")

    def raise_for_status(self) -> None:
        if not self.ok:
            raise HTTPError(self)


def _encode_params(params: Optional[Mapping[str, Any]]) -> str:
    if not params:
        return ""
    items: Iterable[tuple[str, str]] = (
        (key, str(value)) for key, value in params.items()
    )
    return urllib.parse.urlencode(list(items))


def request(
    method: str,
    url: str,
    *,
    params: Optional[Mapping[str, Any]] = None,
    data: Optional[Mapping[str, Any]] = None,
    json_payload: Optional[Any] = None,
    headers: Optional[Mapping[str, str]] = None,
    timeout: Optional[float] = None,
) -> Response:
    """Execute a basic HTTP request using :mod:`urllib.request`."""

    query = _encode_params(params)
    if query:
        separator = "&" if urllib.parse.urlparse(url).query else "?"
        url = f"{url}{separator}{query}"

    body: Optional[bytes] = None
    request_headers: Dict[str, str] = {"User-Agent": "requests-stub"}
    if headers:
        request_headers.update(headers)

    if json_payload is not None:
        body = _json.dumps(json_payload).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")
    elif data is not None:
        body = urllib.parse.urlencode(data).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=request_headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            payload = response.read()
            reason = getattr(response, "reason", "") or ""
            return Response(payload, response.getcode(), dict(response.getheaders()), reason)
    except urllib.error.HTTPError as error:  # pragma: no cover - translated into HTTPError
        payload = error.read()
        response = Response(payload, error.code, dict(error.headers or {}), error.reason)
        raise HTTPError(response) from None
    except urllib.error.URLError as error:  # pragma: no cover - surface like requests
        raise RequestException(str(error)) from error


def get(
    url: str,
    *,
    params: Optional[Mapping[str, Any]] = None,
    headers: Optional[Mapping[str, str]] = None,
    timeout: Optional[float] = None,
) -> Response:
    return request("GET", url, params=params, headers=headers, timeout=timeout)


def post(
    url: str,
    *,
    data: Optional[Mapping[str, Any]] = None,
    json: Optional[Any] = None,
    headers: Optional[Mapping[str, str]] = None,
    timeout: Optional[float] = None,
) -> Response:
    return request("POST", url, data=data, json_payload=json, headers=headers, timeout=timeout)
