from llm.backends.plugins.lobechat import LobeChatBackend, run_lobechat


def test_lobechat_backend_makes_request(monkeypatch):
    calls = {}

    def fake_post(url, json, headers, timeout):
        calls["url"] = url
        calls["json"] = json
        calls["headers"] = headers

        class Resp:
            def raise_for_status(self):
                pass

            def json(self):
                return {"choices": [{"message": {"content": "ok"}}]}

        return Resp()

    monkeypatch.setattr("requests.post", fake_post)
    monkeypatch.setenv("LOBECHAT_API_KEY", "k")
    monkeypatch.setenv("LOBECHAT_BASE_URL", "https://example.com/api")

    backend = LobeChatBackend("m")
    out = backend.run("p")

    assert out == "ok"
    assert calls["url"] == "https://example.com/api/chat/completions"
    assert calls["json"] == {
        "model": "m",
        "messages": [{"role": "user", "content": "p"}],
    }
    assert calls["headers"] == {"Authorization": "Bearer k"}


def test_run_lobechat(monkeypatch):
    calls = []

    class Dummy:
        def __init__(self, model):
            calls.append(("init", model))

        def run(self, prompt: str) -> str:
            calls.append(("run", prompt))
            return "yes"

    monkeypatch.setattr("llm.backends.plugins.lobechat.LobeChatBackend", Dummy)

    result = run_lobechat("hi", "m")
    assert result == "yes"
    assert calls == [("init", "m"), ("run", "hi")]
