from llm.langchain_backend import LangChainBackend
import io
import contextlib
import pytest

pytest.importorskip("requests")

from scripts import ai_router as cli_ai_router
from llm import router


class DummyChain:
    def __init__(self) -> None:
        self.calls = []

    def invoke(self, data):
        self.calls.append(data)
        return "out"


def test_langchain_backend_invokes_chain():
    chain = DummyChain()
    backend = LangChainBackend(chain)
    result = backend.run("hello")
    assert result == "out"
    assert chain.calls == [{"input": "hello"}]


def test_cli_backend_option(monkeypatch):
    def mock_send_prompt(prompt: str, *, local: bool = False, model: str = router.DEFAULT_MODEL) -> str:

        assert prompt == "cli"
        assert model == router.DEFAULT_MODEL
        return "ok"

    monkeypatch.setattr(router, "send_prompt", mock_send_prompt)


    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = cli_ai_router.main(["--backend", "langchain", "cli"])
    assert rc == 0
    assert out.getvalue().strip() == "ok"

def test_run_backend_langchain(monkeypatch):
    calls = []

    def mock_backend(name: str, prompt: str, model: str) -> str:
        assert name == "langchain"
        calls.append(prompt)
        return "done"

    monkeypatch.setattr(router, "_run_backend", mock_backend)
    out = router._run_backend("langchain", "hi", "m")
    assert out == "done"
    assert calls == ["hi"]
