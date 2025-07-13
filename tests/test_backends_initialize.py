from llm import backends


def test_initialize_idempotent(monkeypatch):
    calls = []

    def fake_load() -> None:
        calls.append(True)

    monkeypatch.setattr(backends, "load_backends", fake_load)
    # Reset initialization flag
    monkeypatch.setattr(backends, "_INITIALIZED", False)

    backends.initialize()
    backends.initialize()
    backends.initialize()

    assert calls == [True]
