import json
import pytest

pytest.importorskip("requests")

import time
import importlib

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
    cached = json.loads(cache.read_text())
    assert isinstance(cached.get("timestamp"), int)
    assert cached.get("registry") == result


def test_load_registry_uses_cache_when_offline(monkeypatch, tmp_path):
    cache = tmp_path / "cache.json"
    cache.write_text(
        json.dumps({"timestamp": int(time.time()), "registry": {"plugins": {"y": "pkg"}}})
    )
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


def test_load_registry_skips_network_with_cache(monkeypatch, tmp_path):
    cache = tmp_path / "cache.json"
    cache.write_text(
        json.dumps({"timestamp": int(time.time()), "registry": {"plugins": {"y": "pkg"}}})
    )
    monkeypatch.setattr(plugins, "CACHE_PATH", cache)

    def fail_fetch(url):  # pragma: no cover - should not be called
        raise AssertionError("network called")

    monkeypatch.setattr(plugins, "_fetch_registry", fail_fetch)

    registry = plugins.load_registry(ttl=3600)
    assert registry == {"y": "pkg"}


def test_load_registry_update_forces_fetch(monkeypatch, tmp_path):
    cache = tmp_path / "cache.json"
    cache.write_text(
        json.dumps({"timestamp": int(time.time()), "registry": {"plugins": {"y": "pkg"}}})
    )
    monkeypatch.setattr(plugins, "CACHE_PATH", cache)

    called = False

    def fake_fetch(url):
        nonlocal called
        called = True
        return {"plugins": {"z": "pkg"}}

    monkeypatch.setattr(plugins, "_fetch_registry", fake_fetch)

    registry = plugins.load_registry(update=True)
    assert called
    assert registry == {"z": "pkg"}


def test_load_registry_fetches_when_cache_expired(monkeypatch, tmp_path):
    cache = tmp_path / "cache.json"
    old_ts = int(time.time()) - 100
    cache.write_text(
        json.dumps({"timestamp": old_ts, "registry": {"plugins": {"y": "pkg"}}})
    )
    monkeypatch.setattr(plugins, "CACHE_PATH", cache)

    called = False

    def fake_fetch(url):
        nonlocal called
        called = True
        return {"plugins": {"z": "pkg"}}

    monkeypatch.setattr(plugins, "_fetch_registry", fake_fetch)

    registry = plugins.load_registry(ttl=10)
    assert called
    assert registry == {"z": "pkg"}


def test_load_registry_uses_env_ttl(monkeypatch, tmp_path):
    cache = tmp_path / "cache.json"
    cache.write_text(
        json.dumps({"timestamp": int(time.time()) - 5, "registry": {"plugins": {"x": "pkg"}}})
    )
    monkeypatch.setenv("PLUGIN_REGISTRY_TTL", "1")
    reloaded = importlib.reload(plugins)
    monkeypatch.setattr(reloaded, "CACHE_PATH", cache)

    called = False

    def fake_fetch(url):
        nonlocal called
        called = True
        return {"plugins": {"y": "pkg"}}

    monkeypatch.setattr(reloaded, "_fetch_registry", fake_fetch)

    registry = reloaded.load_registry()
    assert called
    assert registry == {"y": "pkg"}


def test_load_registry_fetches_with_zero_ttl(monkeypatch, tmp_path):
    cache = tmp_path / "cache.json"
    cache.write_text(
        json.dumps({"timestamp": int(time.time()), "registry": {"plugins": {"x": "pkg"}}})
    )
    monkeypatch.setattr(plugins, "CACHE_PATH", cache)

    called = False

    def fake_fetch(url):
        nonlocal called
        called = True
        return {"plugins": {"y": "pkg"}}

    monkeypatch.setattr(plugins, "_fetch_registry", fake_fetch)

    registry = plugins.load_registry(ttl=0)
    assert called
    assert registry == {"y": "pkg"}


def test_load_registry_surfaces_mcp_metadata(monkeypatch, tmp_path):
    cache = tmp_path / "cache.json"
    monkeypatch.setattr(plugins, "CACHE_PATH", cache)

    data = {
        "plugins": {
            "example": {
                "package": "pkg",
                "mcp": {
                    "server_url": "https://example.com",
                    "capabilities": ["x"],
                },
            }
        }
    }

    monkeypatch.setattr(plugins, "_fetch_registry", lambda url: data)
    monkeypatch.setenv("PLUGIN_REGISTRY_URL", "https://example.com")

    registry = plugins.load_registry(raw=True, update=True)
    meta = registry["example"]["mcp"]
    assert meta["server_url"] == "https://example.com"
    assert meta["capabilities"] == ["x"]


def test_example_mcp_plugin_metadata():
    from plugins import example_mcp_plugin

    meta = example_mcp_plugin.mcp_tool()
    assert meta["server_url"] == "https://example.com/mcp"
    assert meta["capabilities"] == ["echo"]


def test_builtin_plugins_present(monkeypatch, tmp_path):
    monkeypatch.setattr(plugins, "CACHE_PATH", tmp_path / "missing.json")

    def raise_exc(*a, **k):
        raise plugins.requests.exceptions.RequestException("boom")

    monkeypatch.setattr(plugins.requests, "get", raise_exc)

    registry = plugins.load_registry()
    expected = {
        "anthropic": "d0ttino-anthropic-plugin",
        "mistral": "d0ttino-mistral-plugin",
        "lmql": "d0ttino-lmql-plugin",
    }
    for name, pkg in expected.items():
        assert registry[name] == pkg
