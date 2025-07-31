import argparse
from pathlib import Path
import json
import time

import pytest

pytest.importorskip("requests")

from scripts import plugins


def test_cmd_sync_recipes_uses_default_dir(monkeypatch, tmp_path):
    packages = {"echo": "echo-pkg", "foo": "foo-pkg"}

    def fake_run(cmd, *a, **k):
        dest = Path(cmd[cmd.index("--target") + 1])
        pkg = cmd[-1]
        (dest / pkg).write_text("installed")

        class Res:
            returncode = 0

        return Res()

    monkeypatch.setattr(plugins, "load_registry", lambda section="plugins", update=False: packages)
    monkeypatch.setattr(plugins.subprocess, "run", fake_run)
    monkeypatch.setattr(plugins, "RECIPE_DOWNLOAD_DIR", tmp_path)

    args = argparse.Namespace(dest=None, update=False)
    rc = plugins._cmd_sync_recipes(args)
    assert rc == 0
    for pkg in packages.values():
        assert (tmp_path / pkg).is_file()


def test_load_registry_cache_miss(monkeypatch, tmp_path):
    """Fetching occurs and cache file is written when missing."""
    cache = tmp_path / "cache.json"
    monkeypatch.setattr(plugins, "CACHE_PATH", cache)

    result = {"plugins": {"a": "pkg"}}

    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return result

    monkeypatch.setattr(plugins.requests, "get", lambda *a, **k: Resp())

    reg = plugins.load_registry()
    assert reg == {"a": "pkg"}
    saved = json.loads(cache.read_text())
    assert saved["registry"] == result


def test_load_registry_cache_hit(monkeypatch, tmp_path):
    """Cached registry is used when TTL has not expired."""
    cache = tmp_path / "cache.json"
    now = int(time.time())
    cache.write_text(json.dumps({"timestamp": now, "registry": {"plugins": {"a": "pkg"}}}))
    monkeypatch.setattr(plugins, "CACHE_PATH", cache)

    def fail_fetch(url):  # pragma: no cover - should not run
        raise AssertionError("fetch")

    monkeypatch.setattr(plugins, "_fetch_registry", fail_fetch)

    reg = plugins.load_registry(ttl=3600)
    assert reg == {"a": "pkg"}


def test_load_registry_corrupt_cache(monkeypatch, tmp_path):
    """Corrupt cache triggers fetch and gets replaced."""
    cache = tmp_path / "cache.json"
    cache.write_text("{invalid")
    monkeypatch.setattr(plugins, "CACHE_PATH", cache)

    result = {"plugins": {"b": "pkg"}}

    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return result

    monkeypatch.setattr(plugins.requests, "get", lambda *a, **k: Resp())

    reg = plugins.load_registry()
    assert reg == {"b": "pkg"}
    loaded = json.loads(cache.read_text())
    assert loaded["registry"] == result


def test_load_registry_force_refresh(monkeypatch, tmp_path):
    """Setting ttl=0 forces a refresh even when cache is fresh."""
    cache = tmp_path / "cache.json"
    now = int(time.time())
    cache.write_text(json.dumps({"timestamp": now, "registry": {"plugins": {"a": "pkg"}}}))
    monkeypatch.setattr(plugins, "CACHE_PATH", cache)

    called = {}

    def fake_fetch(url):
        called["called"] = True
        return {"plugins": {"b": "pkg"}}

    monkeypatch.setattr(plugins, "_fetch_registry", fake_fetch)

    reg = plugins.load_registry(ttl=0)
    assert called.get("called") is True
    assert reg == {"b": "pkg"}

