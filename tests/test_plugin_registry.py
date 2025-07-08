import json

from scripts import plugins


def test_load_registry_fetches_and_caches(monkeypatch, tmp_path):
    cached = tmp_path / "cache.json"
    monkeypatch.setattr(plugins, "CACHE_PATH", cached)

    result = {"x": "pkg"}

    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return result

    def fake_get(url, timeout=None):
        return Resp()

    monkeypatch.setattr(plugins, "requests", type("req", (), {"get": fake_get}))
    monkeypatch.setenv("PLUGIN_REGISTRY_URL", "https://example.com")

    registry = plugins.load_registry()
    assert registry == result
    assert json.loads(cached.read_text()) == result


def test_load_registry_uses_cache_on_error(monkeypatch, tmp_path):
    cached = tmp_path / "cache.json"
    cached.write_text(json.dumps({"y": "pkg"}))
    monkeypatch.setattr(plugins, "CACHE_PATH", cached)

    def fake_get(url, timeout=None):
        raise OSError()

    monkeypatch.setattr(plugins, "requests", type("req", (), {"get": fake_get}))
    monkeypatch.setenv("PLUGIN_REGISTRY_URL", "https://example.com")

    registry = plugins.load_registry()
    assert registry == {"y": "pkg"}


def test_load_registry_defaults_when_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(plugins, "CACHE_PATH", tmp_path / "missing.json")
    monkeypatch.delenv("PLUGIN_REGISTRY_URL", raising=False)

    registry = plugins.load_registry()
    assert registry == plugins.PLUGIN_REGISTRY
