import types
import sys

from llm import etl


def test_partition_document(monkeypatch, tmp_path):
    file = tmp_path / "doc.txt"
    file.write_text("dummy")

    class E:
        def __init__(self, text):
            self.text = text

    def fake_partition(filename):
        assert filename == str(file)
        return [E("a"), E("b")]

    fake_mod = types.SimpleNamespace(partition=fake_partition)
    monkeypatch.setitem(sys.modules, "unstructured.partition.auto", fake_mod)

    chunks = etl.partition_document(file)
    assert chunks == ["a", "b"]


def test_store_embeddings(monkeypatch, tmp_path):
    added = {}

    class FakeCollection:
        def add(self, *, documents, ids):
            added["docs"] = documents
            added["ids"] = ids

    class FakeClient:
        def __init__(self, path):
            added["path"] = path

        def get_or_create_collection(self, name, embedding_function=None):
            added["name"] = name
            added["embed"] = embedding_function
            return FakeCollection()

    fake_emb_mod = types.SimpleNamespace(
        SentenceTransformerEmbeddingFunction=lambda: "embed"
    )
    monkeypatch.setitem(
        sys.modules,
        "chromadb.utils.embedding_functions",
        fake_emb_mod,
    )
    monkeypatch.setitem(sys.modules, "chromadb.utils", types.SimpleNamespace(embedding_functions=fake_emb_mod))
    monkeypatch.setitem(sys.modules, "chromadb", types.SimpleNamespace(PersistentClient=FakeClient))

    coll = etl.store_embeddings(["x"], persist_dir=tmp_path, collection_name="c")
    assert added["path"] == str(tmp_path)
    assert added["name"] == "c"
    assert added["docs"] == ["x"]
    assert added["ids"] == ["doc-0"]
    assert isinstance(coll, FakeCollection)


def test_register_retrieval_nodes(monkeypatch):
    calls = []

    class Graph:
        def add_node(self, name, node):
            calls.append((name, node))

    sentinel = object()

    fake_retrieval = types.SimpleNamespace(ChromaRetriever=lambda c: sentinel)
    monkeypatch.setitem(sys.modules, "langgraph.prebuilt.retrieval", fake_retrieval)
    monkeypatch.setitem(sys.modules, "langgraph.prebuilt", types.SimpleNamespace(retrieval=fake_retrieval))

    g = Graph()
    out = etl.register_retrieval_nodes(g, "coll", node_name="n")
    assert out is g
    assert calls == [("n", sentinel)]
