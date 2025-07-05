from fastapi.testclient import TestClient
import importlib
import os
import sys
import types
from pathlib import Path

import requests

def load_app(send_prompt=lambda p, local=False: f"resp-{p}", apply_palette=lambda n, r: None, state_path: Path | None = None):
    stub_router = types.SimpleNamespace(send_prompt=send_prompt)
    stub_thm = types.SimpleNamespace(apply_palette=apply_palette, REPO_ROOT=Path('.'))
    sys.modules['scripts.ai_router'] = stub_router
    sys.modules['scripts.thm'] = stub_thm
    if state_path is None:
        state_path = Path('state.json')
    os.environ['API_STATE_PATH'] = str(state_path)
    if state_path.exists():
        state_path.unlink()
    if 'api' in sys.modules:
        del sys.modules['api']
    api = importlib.import_module('api')
    return api.app


def test_health(tmp_path):
    app = load_app(state_path=tmp_path / 'state.json')
    client = TestClient(app)
    resp = client.get('/api/health')
    assert resp.status_code == 200
    assert resp.json() == {'status': 'ok'}


def test_stats(tmp_path):
    app = load_app(state_path=tmp_path / 'state.json')

    client = TestClient(app)
    resp = client.get('/api/stats')
    assert resp.status_code == 200
    assert resp.json() == {'queries': 1, 'memory': 2}
    assert calls == ['http://ume/dashboard/stats']


def test_graph(monkeypatch):
    calls = []

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {'nodes': ['n1'], 'edges': ['e1']}

        @staticmethod
        def raise_for_status():
            pass

    resp = client.post('/api/prompt', json={'prompt': 'hello'})
    assert resp.status_code == 200
    resp = client.get('/api/stats')
    assert resp.json() == {'queries': 1, 'memory': 1}


def test_graph(tmp_path):
    app = load_app(state_path=tmp_path / 'state.json')

    client = TestClient(app)
    resp = client.post('/api/prompt', json={'prompt': 'one'})
    assert resp.status_code == 200
    resp = client.post('/api/prompt', json={'prompt': 'two'})
    assert resp.status_code == 200
    resp = client.get('/api/graph')
    assert resp.status_code == 200
    data = resp.json()
    assert len(data['nodes']) == 2
    assert len(data['edges']) == 1



def test_prompt(tmp_path):
    calls = []
    def fake(prompt: str, local: bool = False):
        calls.append(prompt)
        return 'ok-' + prompt
    app = load_app(send_prompt=fake, state_path=tmp_path / 'state.json')
    client = TestClient(app)
    resp = client.post('/api/prompt', json={'prompt': 'hello'})
    assert resp.status_code == 200
    assert resp.json() == {'response': 'ok-hello'}
    assert calls == ['hello']


def test_palette(tmp_path):
    calls = []
    def fake(name: str, repo_root: Path):
        calls.append(name)
    app = load_app(apply_palette=fake, state_path=tmp_path / 'state.json')
    client = TestClient(app)
    resp = client.post('/api/palette', json={'name': 'dracula'})
    assert resp.status_code == 200
    assert resp.json() == {'status': 'applied'}
    assert calls == ['dracula']
