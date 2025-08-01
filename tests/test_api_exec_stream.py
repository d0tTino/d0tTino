import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

import httpx
from api import app
from scripts import ai_exec


@pytest.mark.asyncio
async def test_exec_stream_async_client(monkeypatch):
    monkeypatch.setattr(ai_exec, "plan", lambda goal: ["echo hi"])
    async with httpx.AsyncClient(
        base_url="http://test",
        transport=httpx.ASGITransport(app=app),
    ) as client:
        async with client.stream("GET", "/api/exec", params={"goal": "echo hi"}) as resp:
            lines = [line async for line in resp.aiter_lines() if line]

    assert "data: $ echo hi" in lines
    assert "data: (exit 0)" in lines
