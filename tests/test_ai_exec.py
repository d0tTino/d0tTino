import subprocess

import io
import contextlib
import pytest

pytest.importorskip("requests")

from scripts import ai_exec


def test_plan_uses_primary(monkeypatch):
    calls = []

    def fake_gemini(prompt, model=None):
        calls.append(("gemini", prompt, model))
        return "step1\nstep2"

    def fail_ollama(prompt, model):
        raise AssertionError("ollama should not be called")

    monkeypatch.setattr(ai_exec.router, "run_gemini", fake_gemini)
    monkeypatch.setattr(ai_exec.router, "run_ollama", fail_ollama)
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

    monkeypatch.setattr(ai_exec.router, "run_gemini", failing_gemini)
    monkeypatch.setattr(ai_exec.router, "run_ollama", fake_ollama)
    monkeypatch.setattr(ai_exec, "get_preferred_models", lambda *a, **k: ("g", "o"))

    steps = ai_exec.plan("goal")
    assert steps == ["fallback"]
    assert calls == [
        ("gemini", "goal", "g"),
        ("ollama", "goal", "o"),
    ]


def test_main_invokes_plan(monkeypatch):
    def mock_plan(goal: str, *, config_path=None, analytics=False):
        assert goal == "goal"
        assert str(config_path) == "cfg.json"
        return ["one", "two"]

    monkeypatch.setattr(ai_exec, "plan", mock_plan)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_exec.main(["goal", "--config", "cfg.json"])
    assert rc == 0
    assert out.getvalue().splitlines() == ["one", "two"]


def test_main_notifies(monkeypatch):
    monkeypatch.setattr(ai_exec, "plan", lambda *a, **k: [])
    called = []

    def fake_notify(msg):
        called.append(msg)

    monkeypatch.setattr(ai_exec, "send_notification", fake_notify)
    rc = ai_exec.main(["goal", "--notify"])
    assert rc == 0
    assert called == ["ai-plan completed"]


def test_plan_records_event(monkeypatch):
    monkeypatch.setattr(ai_exec.router, "run_gemini", lambda *a, **k: "step")
    monkeypatch.setattr(ai_exec.router, "run_ollama", lambda *a, **k: "step")
    monkeypatch.setattr(ai_exec, "get_preferred_models", lambda *a, **k: ("g", "o"))
    recorded = []

    def fake_record(name, payload, *, enabled=False):
        recorded.append((name, payload, enabled))

    monkeypatch.setattr(ai_exec, "record_event", fake_record)
    steps = ai_exec.plan("goal", analytics=True)
    assert steps == ["step"]
    name, payload, enabled = recorded[0]
    assert name == "ai-exec-plan"
    assert enabled is True
    assert payload["goal"] == "goal"
    assert payload["step_count"] == 1
    assert "latency_ms" in payload and payload["latency_ms"] >= 0

