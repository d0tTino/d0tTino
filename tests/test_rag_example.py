import sys
import types
import io
import contextlib
from pathlib import Path

import pytest

from llm import etl

from scripts import rag_example


def test_build_graph(monkeypatch):
    outputs = []

    class Graph:
        def __init__(self, *a, **k):
            self.nodes = {}
            self.entry = None

        def add_node(self, name, node):
            self.nodes[name] = node

        def set_entry_point(self, name):
            self.entry = name

        def compile(self):
            graph = self

            class App:
                def invoke(self, state):
                    return graph.nodes[graph.entry](state)

            return App()

    def fake_stategraph(*a, **k):
        return Graph()

    monkeypatch.setitem(
        sys.modules,
        "langgraph.graph",
        types.SimpleNamespace(StateGraph=fake_stategraph),
    )

    def fake_register(graph, collection, *, node_name="retrieve"):
        def run(state):
            outputs.append(state)
            return {"text": "retrieved"}

        graph.add_node(node_name, run)
        return graph

    monkeypatch.setattr(rag_example.etl, "register_retrieval_nodes", fake_register)

    app = rag_example.build_graph("coll")
    result = app.invoke({"query": "hello"})
    assert result == {"text": "retrieved"}
    assert outputs == [{"query": "hello"}]


def test_main_prints_text(monkeypatch, tmp_path):
    out = io.StringIO()
    captured = []

    class FakeCollection:
        pass

    class FakeClient:
        def __init__(self, path):
            captured.append(f"path:{path}")

        def get_or_create_collection(self, name):
            captured.append(f"name:{name}")
            return FakeCollection()

    def fake_build_graph(collection):
        assert isinstance(collection, FakeCollection)

        class App:
            def invoke(self, state):
                captured.append(state)
                return {"text": "ok"}

        return App()

    monkeypatch.setitem(
        sys.modules,
        "chromadb",
        types.SimpleNamespace(PersistentClient=FakeClient),
    )
    monkeypatch.setattr(rag_example, "build_graph", fake_build_graph)

    with contextlib.redirect_stdout(out):
        rc = rag_example.main(
            ["hi", "--persist", str(tmp_path), "--collection", "demo"]
        )

    assert rc == 0
    assert out.getvalue().strip() == "ok"
    assert captured == [f"path:{tmp_path}", "name:demo", {"query": "hi"}]


def test_ingest_and_query(monkeypatch, tmp_path):
    persist = tmp_path / "db"
    persist.mkdir()

    class FakeCollection:
        def __init__(self):
            self.docs: list[str] = []

        def add(self, *, documents, ids):
            self.docs.extend(documents)

    class FakeClient:
        def __init__(self, path):
            assert Path(path) == persist

        def get_or_create_collection(self, name, embedding_function=None):
            assert name == "demo"
            return collection

    fake_emb_mod = types.SimpleNamespace(
        SentenceTransformerEmbeddingFunction=lambda: "embed"
    )
    monkeypatch.setitem(
        sys.modules,
        "chromadb.utils.embedding_functions",
        fake_emb_mod,
    )
    monkeypatch.setitem(sys.modules, "chromadb.utils", types.SimpleNamespace(embedding_functions=fake_emb_mod))
    monkeypatch.setitem(
        sys.modules,
        "chromadb",
        types.SimpleNamespace(PersistentClient=FakeClient),
    )

    collection = FakeCollection()
    coll = etl.store_embeddings(["small"], persist_dir=persist, collection_name="demo")
    assert coll is collection

    outputs = []

    class Graph:
        def __init__(self):
            self.nodes = {}
            self.entry = None

        def add_node(self, name, node):
            self.nodes[name] = node

        def set_entry_point(self, name):
            self.entry = name

        def compile(self):
            graph = self

            class App:
                def invoke(self, state):
                    return graph.nodes[graph.entry](state)

            return App()

    def fake_stategraph(*_a, **_k):
        return Graph()

    monkeypatch.setitem(
        sys.modules,
        "langgraph.graph",
        types.SimpleNamespace(StateGraph=fake_stategraph),
    )

    def fake_register(graph, collection, *, node_name="retrieve"):
        assert collection is coll

        def run(state):
            outputs.append(state)
            return {"text": collection.docs[0]}

        graph.add_node(node_name, run)
        return graph

    monkeypatch.setattr(rag_example.etl, "register_retrieval_nodes", fake_register)

    app = rag_example.build_graph(coll)
    result = app.invoke({"query": "hi"})
    assert result == {"text": "small"}
    assert outputs == [{"query": "hi"}]


def test_store_embeddings_missing_dir(monkeypatch, tmp_path):
    missing = tmp_path / "nope"

    class FakeClient:
        def __init__(self, path):
            if not Path(path).exists():
                raise FileNotFoundError(path)

        def get_or_create_collection(self, name, embedding_function=None):
            return object()

    fake_emb_mod = types.SimpleNamespace(
        SentenceTransformerEmbeddingFunction=lambda: "embed"
    )
    monkeypatch.setitem(
        sys.modules,
        "chromadb.utils.embedding_functions",
        fake_emb_mod,
    )
    monkeypatch.setitem(sys.modules, "chromadb.utils", types.SimpleNamespace(embedding_functions=fake_emb_mod))
    monkeypatch.setitem(
        sys.modules,
        "chromadb",
        types.SimpleNamespace(PersistentClient=FakeClient),
    )

    with pytest.raises(FileNotFoundError):
        etl.store_embeddings(["x"], persist_dir=missing, collection_name="demo")

