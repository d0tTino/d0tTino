import subprocess
import os
import sys
import io
import contextlib
import threading
import time
import pytest
from pathlib import Path

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
        return True

    monkeypatch.setattr(ai_exec, "record_event", fake_record)
    steps = ai_exec.plan("goal", analytics=True)
    assert steps == ["step"]
    name, payload, enabled = recorded[0]
    assert name == "ai-exec-plan"
    assert enabled is True
    assert payload["goal"] == "goal"
    assert payload["step_count"] == 1
    assert "duration_ms" in payload and payload["duration_ms"] >= 0
    assert payload["model_source"] == "remote"


def create_exe(path: Path, contents: str = "#!/usr/bin/env bash\n") -> None:
    path.write_text(contents, encoding="utf-8")
    path.chmod(0o755)


def test_script_runs(monkeypatch, tmp_path: Path) -> None:
    """Verify that ``scripts.ai_exec`` executes a local ``gemini`` binary."""

    # Force the CLI-based backend so the test does not require API keys. We do
    # this by shadowing the ``dspy`` package with a stub that raises
    # ``ImportError``. ``gemini.py`` will then fall back to the simple CLI
    # backend rather than the DSPy implementation.
    stub_dir = tmp_path / "stub"
    (stub_dir / "dspy").mkdir(parents=True)
    (stub_dir / "dspy" / "__init__.py").write_text("raise ImportError('stub')")

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{stub_dir}:{env.get('PYTHONPATH', '')}"

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    create_exe(
        bin_dir / "gemini",
        "#!/usr/bin/env bash\necho step1\necho step2\n",
    )

    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    result = subprocess.run(
        [sys.executable, "-m", "scripts.ai_exec", "goal"],
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    assert result.stdout.splitlines() == ["step1", "step2"]


def test_last_model_remote_thread_safety(monkeypatch):
    monkeypatch.setattr(ai_exec, "get_preferred_models", lambda *a, **k: ("g", "o"))

    def fake_gemini(prompt, model=None):
        if prompt == "remote":
            time.sleep(0.1)
            return "remote-step"
        time.sleep(0.3)
        raise subprocess.CalledProcessError(1, ["gemini"])

    def fake_ollama(prompt, model):
        time.sleep(0.1)
        return "local-step"

    monkeypatch.setattr(ai_exec.router, "run_gemini", fake_gemini)
    monkeypatch.setattr(ai_exec.router, "run_ollama", fake_ollama)

    results = {}

    def run(goal):
        steps = ai_exec.plan(goal)
        results[goal] = (steps, ai_exec.last_model_remote())

    t_remote = threading.Thread(target=run, args=("remote",))
    t_local = threading.Thread(target=run, args=("local",))
    t_remote.start()
    t_local.start()
    t_remote.join()
    t_local.join()

    assert results["remote"] == (["remote-step"], True)
    assert results["local"] == (["local-step"], False)
    assert ai_exec.last_model_remote() is False

