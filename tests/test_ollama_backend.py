import subprocess
import pytest

from llm import router as ai_router
from llm.backends import register_backend
from llm.backends.plugins import ollama as plugin


def test_ollama_backend_runs_command(monkeypatch):
    calls = {}

    def fake_run(cmd, capture_output=True, text=True, check=True):
        calls['cmd'] = cmd

        class Res:
            stdout = 'ok'

        return Res()

    monkeypatch.setattr(subprocess, 'run', fake_run)

    backend = plugin.OllamaBackend('m')
    out = backend.run('p')

    assert out == 'ok'
    assert calls['cmd'] == ['ollama', 'run', 'm', 'p']


@pytest.mark.usefixtures('monkeypatch')
def test_run_ollama_uses_dspy_backend(monkeypatch):
    pytest.importorskip('dspy')  # ensure dependency present

    calls = []

    class Dummy:
        def __init__(self, model):
            calls.append(('init', model))

        def run(self, prompt: str) -> str:
            calls.append(('run', prompt))
            return 'dspy'

    monkeypatch.setattr(plugin, 'OllamaDSPyBackend', Dummy)
    register_backend('ollama', plugin.run_ollama)
    out = ai_router.run_ollama('hi', 'm')

    assert out == 'dspy'
    assert calls == [('init', 'm'), ('run', 'hi')]


def test_run_ollama_without_dspy(monkeypatch):
    calls = []

    class Dummy:
        def __init__(self, model):
            calls.append(('init', model))

        def run(self, prompt: str) -> str:
            calls.append(('run', prompt))
            return 'cli'

    monkeypatch.setattr(plugin, 'OllamaDSPyBackend', None)
    monkeypatch.setattr(plugin, 'OllamaBackend', Dummy)
    register_backend('ollama', plugin.run_ollama)

    out = ai_router.run_ollama('yo', 'm')

    assert out == 'cli'
    assert calls == [('init', 'm'), ('run', 'yo')]
