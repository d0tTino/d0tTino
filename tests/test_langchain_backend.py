from llm.langchain_backend import LangChainBackend
import io
import contextlib
from scripts import ai_router
from llm.backends import register_backend
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
    def mock_run_langchain(prompt: str, model: str) -> str:
        assert prompt == "cli"
        return "ok"

    register_backend("langchain", mock_run_langchain)

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_router.main(["--backend", "langchain", "cli"])
    assert rc == 0
    assert out.getvalue().strip() == "ok"

def test_run_backend_langchain(monkeypatch):
    calls = []

    def mock_run(prompt: str, model: str) -> str:
        calls.append(prompt)
        return "done"

    register_backend("langchain", mock_run)
    out = router._run_backend("langchain", "hi", "m")
    assert out == "done"
    assert calls == ["hi"]
