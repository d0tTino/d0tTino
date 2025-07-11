import json

import logging

from scripts import plugins


def test_default_registry_url_constant_exists():
    assert isinstance(plugins.DEFAULT_REGISTRY_URL, str)


def test_load_registry_fetches_and_caches(monkeypatch, tmp_path):
    cached = tmp_path / "cache.json"
    monkeypatch.setattr(plugins, "CACHE_PATH", cached)

    result = {"plugins": {"x": "pkg"}}

    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return result

    def fake_get(url, timeout=None):
        return Resp()

    monkeypatch.setattr(plugins.requests, "get", fake_get)
    monkeypatch.setenv("PLUGIN_REGISTRY_URL", "https://example.com")

    registry = plugins.load_registry()
    assert registry == {"x": "pkg"}
    assert json.loads(cached.read_text()) == result


def test_load_registry_uses_cache_on_error(monkeypatch, tmp_path):
    cached = tmp_path / "cache.json"
    cached.write_text(json.dumps({"plugins": {"y": "pkg"}}))
    monkeypatch.setattr(plugins, "CACHE_PATH", cached)

    def fake_get(*args, **kwargs):
        raise plugins.requests.exceptions.RequestException("boom")

    monkeypatch.setattr(plugins.requests, "get", fake_get)
    monkeypatch.setenv("PLUGIN_REGISTRY_URL", "https://example.com")

    registry = plugins.load_registry()
    assert registry == {"y": "pkg"}


def test_load_registry_logs_warning(monkeypatch, tmp_path, caplog):
    cached = tmp_path / "cache.json"
    cached.write_text(json.dumps({"plugins": {"y": "pkg"}}))
    monkeypatch.setattr(plugins, "CACHE_PATH", cached)

    def fake_get(url, timeout=None):
        raise plugins.requests.exceptions.RequestException("boom")

    monkeypatch.setattr(plugins.requests, "get", fake_get)
    monkeypatch.setenv("PLUGIN_REGISTRY_URL", "https://example.com")

    with caplog.at_level(logging.WARNING):
        registry = plugins.load_registry()

    assert registry == {"y": "pkg"}
    assert any("Failed to fetch" in r.message for r in caplog.records)
    assert any("cached registry" in r.message for r in caplog.records)


def test_load_registry_defaults_when_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(plugins, "CACHE_PATH", tmp_path / "missing.json")
    monkeypatch.delenv("PLUGIN_REGISTRY_URL", raising=False)

    def fake_get(*args, **kwargs):
        raise plugins.requests.exceptions.RequestException("boom")

    monkeypatch.setattr(plugins.requests, "get", fake_get)

    registry = plugins.load_registry()
    assert registry == plugins.PLUGIN_REGISTRY


def test_load_registry_ignores_invalid_data(monkeypatch, tmp_path):
    monkeypatch.setattr(plugins, "CACHE_PATH", tmp_path / "missing.json")

    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return ["bad"]

    def fake_get(*args, **kwargs):
        return Resp()

    monkeypatch.setattr(plugins.requests, "get", fake_get)
    monkeypatch.setenv("PLUGIN_REGISTRY_URL", "https://example.com")

    registry = plugins.load_registry()
    assert registry == plugins.PLUGIN_REGISTRY


def test_load_registry_ignores_invalid_cache(monkeypatch, tmp_path):
    cached = tmp_path / "cache.json"
    cached.write_text(json.dumps(["bad"]))
    monkeypatch.setattr(plugins, "CACHE_PATH", cached)

    def fake_get(url, timeout=None):
        raise plugins.requests.exceptions.RequestException("boom")

    monkeypatch.setattr(plugins.requests, "get", fake_get)
    monkeypatch.setenv("PLUGIN_REGISTRY_URL", "https://example.com")

    registry = plugins.load_registry()
    assert registry == plugins.PLUGIN_REGISTRY


def test_load_registry_rejects_bad_entries(monkeypatch, tmp_path):
    monkeypatch.setattr(plugins, "CACHE_PATH", tmp_path / "missing.json")

    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"plugins": {"ok": "pkg", "bad": 123}}

    def fake_get(*args, **kwargs):
        return Resp()

    monkeypatch.setattr(plugins.requests, "get", fake_get)
    monkeypatch.setenv("PLUGIN_REGISTRY_URL", "https://example.com")

    registry = plugins.load_registry()
    assert registry == plugins.PLUGIN_REGISTRY


def test_load_registry_defaults_when_download_fails(monkeypatch, tmp_path):
    monkeypatch.setattr(plugins, "CACHE_PATH", tmp_path / "missing.json")

    def fake_get(*args, **kwargs):
        raise plugins.requests.exceptions.RequestException("boom")

    monkeypatch.setattr(plugins.requests, "get", fake_get)
    monkeypatch.setenv("PLUGIN_REGISTRY_URL", "https://example.com")

    registry = plugins.load_registry()
    assert registry == plugins.PLUGIN_REGISTRY


def test_load_registry_defaults_on_invalid_schema(monkeypatch, tmp_path):
    monkeypatch.setattr(plugins, "CACHE_PATH", tmp_path / "missing.json")

    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"plugins": {"ok": ["pkg"]}}

    def fake_get(*args, **kwargs):
        return Resp()

    monkeypatch.setattr(plugins.requests, "get", fake_get)
    monkeypatch.setenv("PLUGIN_REGISTRY_URL", "https://example.com")

    registry = plugins.load_registry()
    assert registry == plugins.PLUGIN_REGISTRY


def test_load_registry_recipes_section(monkeypatch, tmp_path):
    cached = tmp_path / "cache.json"
    monkeypatch.setattr(plugins, "CACHE_PATH", cached)

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
    cached = tmp_path / "cache.json"
    monkeypatch.setattr(plugins, "CACHE_PATH", cached)
    monkeypatch.delenv("PLUGIN_REGISTRY_URL", raising=False)

    data = {"plugins": {"z": "pkg"}}

    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return data

    def fake_get(url, timeout=None):
        assert url == plugins.DEFAULT_REGISTRY_URL
        return Resp()

    monkeypatch.setattr(plugins.requests, "get", fake_get)

    registry = plugins.load_registry()
    assert registry == {"z": "pkg"}
