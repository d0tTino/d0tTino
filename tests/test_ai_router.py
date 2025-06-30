import io
import contextlib
import subprocess

from scripts import ai_router


def test_send_prompt_calls_gemini(monkeypatch):
    def mock_run_gemini(prompt, model=None):
        return f"gemini:{prompt}:{model}"

    def fail_run_ollama(prompt, model):
        raise AssertionError("ollama should not be called")

    monkeypatch.setattr(ai_router, "run_gemini", mock_run_gemini)
    monkeypatch.setattr(ai_router, "run_ollama", fail_run_ollama)

    out = ai_router.send_prompt("hello", model="g1")
    assert out == "gemini:hello:g1"


def test_send_prompt_falls_back_to_ollama(monkeypatch):
    def mock_run_gemini(prompt, model=None):
        raise subprocess.CalledProcessError(1, ["gemini"])

    def mock_run_ollama(prompt, model):
        return f"ollama:{prompt}:{model}"

    monkeypatch.setattr(ai_router, "run_gemini", mock_run_gemini)
    monkeypatch.setattr(ai_router, "run_ollama", mock_run_ollama)

    out = ai_router.send_prompt("hi", model="o1")
    assert out == "ollama:hi:o1"


def test_send_prompt_local(monkeypatch):
    def fail_run_gemini(prompt, model=None):
        raise AssertionError("gemini should not be called")

    def mock_run_ollama(prompt, model):
        return f"ollama:{prompt}:{model}"

    monkeypatch.setattr(ai_router, "run_gemini", fail_run_gemini)
    monkeypatch.setattr(ai_router, "run_ollama", mock_run_ollama)

    out = ai_router.send_prompt("yo", local=True, model="o2")
    assert out == "ollama:yo:o2"


def test_cli_invokes_send_prompt(monkeypatch):
    def mock_send_prompt(prompt, *, local=False, model=ai_router.DEFAULT_MODEL):
        assert prompt == "cli"
        assert local is True
        assert model == "m"
        return "ok"

    monkeypatch.setattr(ai_router, "send_prompt", mock_send_prompt)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_router.main(["--local", "--model", "m", "cli"])
    assert rc == 0
    assert out.getvalue().strip() == "ok"
