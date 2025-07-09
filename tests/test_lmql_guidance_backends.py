import pytest

from llm import backends
backends.load_backends()
LMQLBackend = backends.LMQLBackend
GuidanceBackend = backends.GuidanceBackend


def test_lmql_backend_returns_string():
    pytest.importorskip("lmql")  # ensure optional dependency present
    backend = LMQLBackend("m")
    assert backend.run("p") == "lmql:p:m"


def test_guidance_backend_returns_string():
    pytest.importorskip("guidance")  # ensure optional dependency present
    backend = GuidanceBackend("m")
    assert backend.run("p") == "guidance:p:m"
