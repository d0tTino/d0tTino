import io
import json
import contextlib
import sys
import os
import subprocess
import pytest

from scripts import ai_router as cli_ai_router
from llm import router, ai_router as llm_router
from llm.backends import register_backend

# Mirror routing helpers from ``llm.router`` onto ``llm_router`` so they can be
# patched independently for tests.
llm_router.run_gemini = router.run_gemini
llm_router.run_ollama = router.run_ollama
llm_router.run_openrouter = router.run_openrouter
llm_router.DEFAULT_COMPLEXITY_THRESHOLD = router.DEFAULT_COMPLEXITY_THRESHOLD


def _send_prompt(prompt: str, *, local: bool = False, model: str = router.DEFAULT_MODEL) -> str:
    """Send ``prompt`` using helpers attached to ``llm_router``."""
    primary, fallback = router._preferred_backends()
    order: list[str] = []

    env_mode = os.environ.get("LLM_ROUTING_MODE", "auto").lower()
    if local or env_mode == "local":
        if fallback:
            order.append(fallback)
    else:
        if env_mode == "remote":
            order.append(primary)
            if fallback:
                order.append(fallback)
        else:  # auto
            try:
                threshold = int(os.environ.get("LLM_COMPLEXITY_THRESHOLD", llm_router.DEFAULT_COMPLEXITY_THRESHOLD))
            except ValueError:
                threshold = llm_router.DEFAULT_COMPLEXITY_THRESHOLD
            complexity = router.estimate_prompt_complexity(prompt)
            if complexity > threshold:
                order.append(primary)
                if fallback:
                    order.append(fallback)
            else:
                if fallback:
                    order.append(fallback)
                order.append(primary)
    for backend_name in order:
        try:
            if backend_name == "gemini":
                return llm_router.run_gemini(prompt, model)
            if backend_name == "ollama":
                return llm_router.run_ollama(prompt, model)
            if backend_name == "openrouter":
                return llm_router.run_openrouter(prompt, model)
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    raise RuntimeError("Unable to process prompt")


llm_router.send_prompt = _send_prompt

ai_router = cli_ai_router


def _set_env(monkeypatch, primary="gemini", fallback="ollama"):
    monkeypatch.setenv("LLM_PRIMARY_BACKEND", primary)
    if fallback is not None:
        monkeypatch.setenv("LLM_FALLBACK_BACKEND", fallback)
    else:
        monkeypatch.delenv("LLM_FALLBACK_BACKEND", raising=False)


def test_send_prompt_uses_local_for_simple_prompt(monkeypatch):
    _set_env(monkeypatch, "gemini", "ollama")

    def fail_run_gemini(prompt, model=None):
        raise AssertionError("gemini should not be called")

    def mock_run_ollama(prompt, model):
        return f"ollama:{prompt}:{model}"

    monkeypatch.setattr(router, "run_gemini", fail_run_gemini)
    register_backend("gemini", router.run_gemini)
    monkeypatch.setattr(router, "run_ollama", mock_run_ollama)
    register_backend("ollama", router.run_ollama)

    out = router.send_prompt("hello", model="g1")
    assert out == "ollama:hello:g1"


def test_send_prompt_uses_primary_for_complex_prompt(monkeypatch):
    _set_env(monkeypatch, "gemini", "ollama")

    long_prompt = " ".join(["word"] * (router.DEFAULT_COMPLEXITY_THRESHOLD + 1))

    def mock_run_gemini(prompt, model=None):
        return f"gemini:{prompt}:{model}"

    def fail_run_ollama(prompt, model):
        raise AssertionError("ollama should not be called")

    monkeypatch.setattr(router, "run_gemini", mock_run_gemini)
    register_backend("gemini", router.run_gemini)
    monkeypatch.setattr(router, "run_ollama", fail_run_ollama)
    register_backend("ollama", router.run_ollama)

    out = router.send_prompt(long_prompt, model="g1")
    assert out.startswith("gemini:")


def test_send_prompt_local(monkeypatch):
    _set_env(monkeypatch, "gemini", "ollama")

    def fail_run_gemini(prompt, model=None):
        raise AssertionError("gemini should not be called")

    def mock_run_ollama(prompt, model):
        return f"ollama:{prompt}:{model}"

    monkeypatch.setattr(router, "run_gemini", fail_run_gemini)
    register_backend("gemini", router.run_gemini)
    monkeypatch.setattr(router, "run_ollama", mock_run_ollama)
    register_backend("ollama", router.run_ollama)

    out = router.send_prompt("yo", local=True, model="o2")
    assert out == "ollama:yo:o2"


def test_env_forces_remote(monkeypatch):
    _set_env(monkeypatch, "gemini", "ollama")
    monkeypatch.setenv("LLM_ROUTING_MODE", "remote")

    def mock_run_gemini(prompt, model=None):
        return f"gemini:{prompt}:{model}"

    def fail_run_ollama(prompt, model):
        raise AssertionError("ollama should not be called")

    monkeypatch.setattr(router, "run_gemini", mock_run_gemini)
    register_backend("gemini", router.run_gemini)
    monkeypatch.setattr(router, "run_ollama", fail_run_ollama)
    register_backend("ollama", router.run_ollama)

    out = router.send_prompt("short", model="g1")
    assert out == "gemini:short:g1"


def test_env_complexity_threshold(monkeypatch):
    _set_env(monkeypatch, "gemini", "ollama")
    monkeypatch.setenv("LLM_COMPLEXITY_THRESHOLD", "1")

    def mock_run_gemini(prompt, model=None):
        return f"gemini:{prompt}:{model}"

    def fail_run_ollama(prompt, model):
        raise AssertionError("ollama should not be called")

    monkeypatch.setattr(router, "run_gemini", mock_run_gemini)
    register_backend("gemini", router.run_gemini)
    monkeypatch.setattr(router, "run_ollama", fail_run_ollama)
    register_backend("ollama", router.run_ollama)

    out = router.send_prompt("two words", model="g1")
    assert out == "gemini:two words:g1"


def test_invalid_complexity_threshold(monkeypatch):
    _set_env(monkeypatch, "gemini", "ollama")
    monkeypatch.setenv("LLM_COMPLEXITY_THRESHOLD", "invalid")


    long_prompt = " ".join(["word"] * (router.DEFAULT_COMPLEXITY_THRESHOLD + 1))


    def mock_run_gemini(prompt, model=None):
        return f"gemini:{prompt}:{model}"

    def fail_run_ollama(prompt, model):  # pragma: no cover - ensure unused

        raise AssertionError("ollama should not be called")

    monkeypatch.setattr(router, "run_gemini", mock_run_gemini)
    monkeypatch.setattr(router, "run_ollama", fail_run_ollama)

    out = router.send_prompt(long_prompt, model="g1")

    assert out.startswith("gemini:")


def test_cli_invokes_send_prompt(monkeypatch):
    def mock_send_prompt(prompt, *, local=False, model=router.DEFAULT_MODEL):
        assert prompt == "cli"
        assert local is True
        assert model == "m"
        return "ok"

    monkeypatch.setattr(router, "send_prompt", mock_send_prompt)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = cli_ai_router.main(["--local", "--model", "m", "cli"])
    assert rc == 0
    assert out.getvalue().strip() == "ok"


def test_cli_reads_stdin(monkeypatch):
    def mock_send_prompt(prompt, *, local=False, model=router.DEFAULT_MODEL):
        assert prompt == "from-stdin"
        assert local is False
        assert model == router.DEFAULT_MODEL
        return "done"

    monkeypatch.setattr(router, "send_prompt", mock_send_prompt)
    out = io.StringIO()
    stdin = io.StringIO("from-stdin")
    monkeypatch.setattr(sys, "stdin", stdin)
    with contextlib.redirect_stdout(out):
        rc = cli_ai_router.main(["-"])
    assert rc == 0
    assert out.getvalue() == "done\n"


def test_get_preferred_models_config_override(tmp_path, monkeypatch):
    cfg = {"primary_model": "p", "fallback_model": "f"}
    config_file = tmp_path / "cfg.json"
    config_file.write_text(json.dumps(cfg))
    primary, fallback = llm_router.get_preferred_models("d1", "d2", config_path=config_file)
    assert (primary, fallback) == ("p", "f")

    config_file2 = tmp_path / "env.json"
    config_file2.write_text(json.dumps({"primary_model": "envp"}))
    monkeypatch.setenv("LLM_CONFIG_PATH", str(config_file2))
    primary2, fallback2 = llm_router.get_preferred_models("d3", "fb")
    assert (primary2, fallback2) == ("envp", "fb")


def test_run_gemini_uses_dspy_backend(monkeypatch):
    dspy = pytest.importorskip("dspy")  # noqa: F841 - ensure dependency present

    calls = []

    class Dummy:
        def __init__(self, model=None):
            calls.append(("init", model))

        def run(self, prompt: str) -> str:
            calls.append(("run", prompt))
            return "dspy"

    class Fail:
        def __init__(self, *a, **k):
            raise AssertionError("GeminiBackend should not be used")

    monkeypatch.setattr(router, "GeminiDSPyBackend", Dummy)
    monkeypatch.setattr(router, "GeminiBackend", Fail)

    out = router.run_gemini("hi", model="m")
    assert out == "dspy"
    assert calls == [("init", "m"), ("run", "hi")]


def test_send_prompt_prefers_dspy(monkeypatch):
    dspy = pytest.importorskip("dspy")  # noqa: F841
    _set_env(monkeypatch, "gemini", "ollama")
    monkeypatch.setenv("LLM_ROUTING_MODE", "remote")

    class Dummy:
        def __init__(self, model=None):
            self.model = model

        def run(self, prompt: str) -> str:
            return f"dspy:{prompt}:{self.model}"

    class FailBackend:
        def __init__(self, *a, **k):
            raise AssertionError("GeminiBackend should not be used")

    def fail_ollama(prompt: str, model: str):  # pragma: no cover - ensure unused
        raise AssertionError("ollama should not be called")

    monkeypatch.setattr(router, "GeminiDSPyBackend", Dummy)
    monkeypatch.setattr(router, "GeminiBackend", FailBackend)
    monkeypatch.setattr(router, "run_ollama", fail_ollama)
    register_backend("gemini", router.run_gemini)
    register_backend("ollama", router.run_ollama)

    out = router.send_prompt("msg", model="m")
    assert out == "dspy:msg:m"

