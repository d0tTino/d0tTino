import sys
import types
import io
import contextlib

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
