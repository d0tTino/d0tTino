import subprocess

import scripts.ai_router as ai_router


def _setup(monkeypatch, outcomes):
    calls = []

    def fake_run(cmd, check=True, *a, **kw):
        calls.append(cmd)
        outcome = outcomes.get(cmd[0])
        if isinstance(outcome, Exception):
            raise outcome
        return subprocess.CompletedProcess(cmd, outcome or 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    return calls


def test_explicit_gemini(monkeypatch):
    calls = _setup(monkeypatch, {})
    ai_router.main(["--backend", "gemini", "hello"])
    assert calls == [["gemini", "hello"]]


def test_explicit_ollama(monkeypatch):
    calls = _setup(monkeypatch, {})
    ai_router.main(["--backend", "ollama", "--model", "foo", "hello"])
    assert calls == [["ollama", "run", "foo", "hello"]]


def test_auto_fallback(monkeypatch):
    calls = _setup(monkeypatch, {"gemini": subprocess.CalledProcessError(1, ["gemini", "hello"])})
    ai_router.main(["--model", "bar", "hello"])
    assert calls == [["gemini", "hello"], ["ollama", "run", "bar", "hello"]]


def test_auto_fallback_missing_cli(monkeypatch):
    calls = _setup(monkeypatch, {"gemini": FileNotFoundError()})
    ai_router.main(["--model", "baz", "hello"])
    assert calls == [["gemini", "hello"], ["ollama", "run", "baz", "hello"]]


def test_failure_when_both_backends_fail(monkeypatch):
    calls = _setup(
        monkeypatch,
        {
            "gemini": subprocess.CalledProcessError(1, ["gemini", "hello"]),
            "ollama": subprocess.CalledProcessError(5, ["ollama", "run", "qux", "hello"]),
        },
    )
    rc = ai_router.main(["--model", "qux", "hello"])
    assert rc == 5
    assert calls == [["gemini", "hello"], ["ollama", "run", "qux", "hello"]]
