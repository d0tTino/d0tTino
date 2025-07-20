import json
import pytest

pytest.importorskip("requests")

from scripts import plugins


def test_default_registry_url_constant_exists():
    assert isinstance(plugins.DEFAULT_REGISTRY_URL, str)


def test_fetch_registry_saves_cache(monkeypatch, tmp_path):
    cache = tmp_path / "cache.json"
    monkeypatch.setattr(plugins, "CACHE_PATH", cache)

    result = {"plugins": {"x": "pkg"}}

    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return result

    monkeypatch.setattr(plugins.requests, "get", lambda *a, **k: Resp())

    data = plugins._fetch_registry("https://example.com")
    assert data == result
    assert json.loads(cache.read_text()) == result


def test_load_registry_uses_cache_when_offline(monkeypatch, tmp_path):
    cache = tmp_path / "cache.json"
    cache.write_text(json.dumps({"plugins": {"y": "pkg"}}))
    monkeypatch.setattr(plugins, "CACHE_PATH", cache)

    def raise_exc(*a, **k):
        raise plugins.requests.exceptions.RequestException("boom")

    monkeypatch.setattr(plugins.requests, "get", raise_exc)
    monkeypatch.setenv("PLUGIN_REGISTRY_URL", "https://example.com")

    registry = plugins.load_registry()
    assert registry == {"y": "pkg"}


def test_load_registry_defaults_without_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(plugins, "CACHE_PATH", tmp_path / "missing.json")

    def raise_exc(*a, **k):
        raise plugins.requests.exceptions.RequestException("boom")

    monkeypatch.setattr(plugins.requests, "get", raise_exc)
    registry = plugins.load_registry()
    assert registry == plugins.PLUGIN_REGISTRY


def test_load_registry_recipes_section(monkeypatch, tmp_path):
    cache = tmp_path / "cache.json"
    monkeypatch.setattr(plugins, "CACHE_PATH", cache)

    data = {"plugins": {}, "recipes": {"echo": "pkg"}}

    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return data

    monkeypatch.setattr(plugins.requests, "get", lambda *a, **k: Resp())
    monkeypatch.setenv("PLUGIN_REGISTRY_URL", "https://example.com")

    registry = plugins.load_registry("recipes")
    assert registry == {"echo": "pkg"}


def test_load_registry_uses_default_url(monkeypatch, tmp_path):
    cache = tmp_path / "cache.json"
    monkeypatch.setattr(plugins, "CACHE_PATH", cache)
    monkeypatch.delenv("PLUGIN_REGISTRY_URL", raising=False)

    result = {"plugins": {"z": "pkg"}}

    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return result

    def fake_get(url, timeout=None):
        assert url == plugins.DEFAULT_REGISTRY_URL
        return Resp()

    monkeypatch.setattr(plugins.requests, "get", fake_get)

    registry = plugins.load_registry()
    assert registry == {"z": "pkg"}

