import subprocess
import io
import contextlib

from scripts import ai_exec


def test_plan_uses_primary(monkeypatch):
    calls = []

    def fake_gemini(prompt, model=None):
        calls.append(("gemini", prompt, model))
        return "step1\nstep2"

    def fail_ollama(prompt, model):
        raise AssertionError("ollama should not be called")

    monkeypatch.setattr(ai_exec.ai_router, "run_gemini", fake_gemini)
    monkeypatch.setattr(ai_exec.ai_router, "run_ollama", fail_ollama)
    monkeypatch.setattr(ai_exec, "get_preferred_models", lambda *a, **k: ("g", "o"))

    steps = ai_exec.plan("goal")
    assert steps == ["step1", "step2"]
    assert calls == [("gemini", "goal", "g")]


def test_plan_falls_back(monkeypatch):
    calls = []

    def failing_gemini(prompt, model=None):
        calls.append(("gemini", prompt, model))
        raise subprocess.CalledProcessError(1, ["gemini"])

    def fake_ollama(prompt, model):
        calls.append(("ollama", prompt, model))
        return "fallback"

    monkeypatch.setattr(ai_exec.ai_router, "run_gemini", failing_gemini)
    monkeypatch.setattr(ai_exec.ai_router, "run_ollama", fake_ollama)
    monkeypatch.setattr(ai_exec, "get_preferred_models", lambda *a, **k: ("g", "o"))

    steps = ai_exec.plan("goal")
    assert steps == ["fallback"]
    assert calls == [
        ("gemini", "goal", "g"),
        ("ollama", "goal", "o"),
    ]


def test_main_invokes_plan(monkeypatch):
    def mock_plan(goal: str, *, config_path=None):
        assert goal == "goal"
        assert config_path == "cfg.json"
        return ["one", "two"]

    monkeypatch.setattr(ai_exec, "plan", mock_plan)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_exec.main(["goal", "--config", "cfg.json"])
    assert rc == 0
    assert out.getvalue().splitlines() == ["one", "two"]
