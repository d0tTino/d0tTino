import subprocess
import sys
import time

import pytest
from fastapi.testclient import TestClient
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

