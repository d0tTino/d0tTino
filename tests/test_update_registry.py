import json

from scripts import update_registry, plugins


def test_update_registry_check_recipes(tmp_path, monkeypatch):
    data = {"plugins": plugins.PLUGIN_REGISTRY, "recipes": {"echo": "old"}}
    reg = tmp_path / "plugin-registry.json"
    reg.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(update_registry, "REGISTRY_PATH", reg)
    orig_load = update_registry.load_registry
    monkeypatch.setattr(update_registry, "load_registry", lambda path=reg: orig_load(path))
    rc = update_registry.main(["--check"])
    assert rc == 1
    assert json.loads(reg.read_text(encoding="utf-8")) == data


def test_update_registry_rewrites_outdated_file(tmp_path, monkeypatch):
    reg = tmp_path / "plugin-registry.json"
    reg.write_text(json.dumps({"plugins": {}, "recipes": {}}), encoding="utf-8")
    monkeypatch.setattr(update_registry, "REGISTRY_PATH", reg)
    orig_load = update_registry.load_registry
    monkeypatch.setattr(update_registry, "load_registry", lambda path=reg: orig_load(path))
    rc = update_registry.main([])
    assert rc == 0
    expected = {"plugins": plugins.PLUGIN_REGISTRY, "recipes": plugins.RECIPE_REGISTRY}
    assert json.loads(reg.read_text(encoding="utf-8")) == expected
