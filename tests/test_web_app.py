import subprocess
import sys
import time

import pytest
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from api import app

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

