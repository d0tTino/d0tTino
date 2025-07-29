import subprocess
import sys
import time

import pytest

pytest.importorskip("httpx")
pytest.importorskip("fastapi")

import httpx
from fastapi.testclient import TestClient
from fastapi import FastAPI
import asyncio
import threading
import requests
import json
import api
from api import app
from scripts import ai_exec

pytest.importorskip("uvicorn")

def test_fastapi_app_starts(tmp_path):
    log = tmp_path / 'out.txt'
    with log.open('w') as log_file:
        proc = subprocess.Popen(
            [
                sys.executable,
                '-m',
                'uvicorn',
                'api:app',
                '--port',
                '8000',
            ],
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        try:
            time.sleep(5)
        finally:
            proc.terminate()
            proc.wait(timeout=10)
    output = log.read_text(encoding='utf-8')
    assert 'Application startup complete' in output or 'Uvicorn running on' in output


def test_health_endpoint():
    client = TestClient(app)
    resp = client.get('/api/health')
    assert resp.status_code == 200
    assert resp.json() == {'status': 'ok'}


def test_plan_and_exec(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr(ai_exec, 'plan', lambda goal: ['echo test'])

    resp = client.post('/api/plan', json={'goal': 'x'})
    assert resp.status_code == 200
    assert resp.json() == {'steps': ['echo test']}

    with client.stream('GET', '/api/exec', params={'goal': 'x'}) as r:
        lines = [line for line in r.iter_lines() if line]

    assert any('$ echo test' in line for line in lines)
    assert any('test' in line for line in lines)


@pytest.mark.asyncio
async def test_exec_stream_async(monkeypatch):
    monkeypatch.setattr(ai_exec, 'plan', lambda goal: ['echo one', 'echo two'])

    async with httpx.AsyncClient(
        base_url="http://test",
        transport=httpx.ASGITransport(app=app),
    ) as client:
        async with client.stream("GET", "/api/exec", params={"goal": "x"}) as response:
            lines = [line async for line in response.aiter_lines() if line]

    assert lines == [
        'data: $ echo one',
        'data: one',
        'data: (exit 0)',
        'data: $ echo two',
        'data: two',
        'data: (exit 0)',
    ]


@pytest.mark.asyncio
async def test_get_stats_and_graph_local(monkeypatch, tmp_path):
    monkeypatch.setattr(api, 'UME_API_URL', None)
    state_file = tmp_path / 'state.json'
    monkeypatch.setattr(api, 'STATE_PATH', state_file)
    state = {
        'queries': 2,
        'nodes': [{'id': 1, 'text': 'a'}, {'id': 2, 'text': 'b'}],
        'edges': [{'source': 1, 'target': 2}],
    }
    state_file.write_text(json.dumps(state), encoding='utf-8')

    stats = await api.get_stats()
    graph = await api.get_graph()

    assert stats == {'queries': 2, 'memory': 2}
    assert graph == {'nodes': state['nodes'], 'edges': state['edges']}


@pytest.mark.asyncio
async def test_get_stats_and_graph_remote(monkeypatch, tmp_path):
    remote = FastAPI()

    @remote.get('/dashboard/stats')
    async def _stats():
        return {'queries': 5, 'memory': 42}

    @remote.get('/graph')
    async def _graph():
        return {'nodes': ['n'], 'edges': ['e']}

    transport = httpx.ASGITransport(app=remote)
    async_client = httpx.AsyncClient(base_url='http://ume', transport=transport)

    def fake_get(url, timeout=None):
        result: httpx.Response | None = None
        exc: Exception | None = None

        def _run() -> None:
            nonlocal result, exc
            try:
                result = asyncio.run(async_client.get(url, timeout=timeout))
            except Exception as e:  # pragma: no cover - debug helper
                exc = e

        thread = threading.Thread(target=_run)
        thread.start()
        thread.join()
        if exc:
            raise exc
        assert result is not None
        return result

    monkeypatch.setattr(api, 'UME_API_URL', 'http://ume')
    monkeypatch.setattr(requests, 'get', fake_get)
    state_file = tmp_path / 'state.json'
    monkeypatch.setattr(api, 'STATE_PATH', state_file)
    state_file.write_text(json.dumps({'queries': 1, 'nodes': [], 'edges': []}), encoding='utf-8')

    stats = await api.get_stats()
    graph = await api.get_graph()

    assert stats == {'queries': 5, 'memory': 42}
    assert graph == {'nodes': ['n'], 'edges': ['e']}
    await async_client.aclose()
    

@pytest.mark.asyncio
async def test_get_stats_and_graph_remote_timeout(monkeypatch, tmp_path):
    def fake_get(url, timeout=None):
        raise requests.exceptions.Timeout

    monkeypatch.setattr(api, 'UME_API_URL', 'http://ume')
    monkeypatch.setattr(requests, 'get', fake_get)
    state_file = tmp_path / 'state.json'
    monkeypatch.setattr(api, 'STATE_PATH', state_file)
    state = {'queries': 3, 'nodes': [{'id': 1}], 'edges': []}
    state_file.write_text(json.dumps(state), encoding='utf-8')

    stats = await api.get_stats()
    graph = await api.get_graph()

    assert stats == {'queries': 3, 'memory': 1}
    assert graph == {'nodes': state['nodes'], 'edges': state['edges']}

