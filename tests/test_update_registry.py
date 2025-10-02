import json

import json

from scripts import update_registry, plugins


def test_update_registry_check_detects_changes(tmp_path, monkeypatch):
    reg = tmp_path / "plugin-registry.json"
    reg.write_text(json.dumps({"name": "old", "version": "0", "commands": [], "taskTemplates": []}))
    monkeypatch.setattr(update_registry, "REGISTRY_PATH", reg)
    orig_load = update_registry.load_registry
    monkeypatch.setattr(update_registry, "load_registry", lambda path=reg: orig_load(path))
    rc = update_registry.main(["--check"])
    assert rc == 1
    assert json.loads(reg.read_text(encoding="utf-8"))["name"] == "old"


def test_update_registry_rewrites_outdated_file(tmp_path, monkeypatch):
    reg = tmp_path / "plugin-registry.json"
    reg.write_text(json.dumps({"name": "old", "version": "0", "commands": [], "taskTemplates": []}), encoding="utf-8")
    monkeypatch.setattr(update_registry, "REGISTRY_PATH", reg)
    orig_load = update_registry.load_registry
    monkeypatch.setattr(update_registry, "load_registry", lambda path=reg: orig_load(path))
    rc = update_registry.main([])
    assert rc == 0
    assert json.loads(reg.read_text(encoding="utf-8")) == plugins._DEFAULT_REGISTRY_RAW


def test_update_registry_creates_missing_file(tmp_path, monkeypatch):
    reg = tmp_path / "plugin-registry.json"
    monkeypatch.setattr(update_registry, "REGISTRY_PATH", reg)
    orig_load = update_registry.load_registry
    monkeypatch.setattr(update_registry, "load_registry", lambda path=reg: orig_load(path))
    rc = update_registry.main([])
    assert rc == 0
    assert json.loads(reg.read_text(encoding="utf-8")) == plugins._DEFAULT_REGISTRY_RAW


def test_update_registry_malformed_json(tmp_path, monkeypatch, capsys):
    reg = tmp_path / "plugin-registry.json"
    reg.write_text("{ bad json }", encoding="utf-8")
    monkeypatch.setattr(update_registry, "REGISTRY_PATH", reg)
    orig_load = update_registry.load_registry
    monkeypatch.setattr(update_registry, "load_registry", lambda path=reg: orig_load(path))
    rc = update_registry.main([])
    captured = capsys.readouterr()
    assert rc == 1
    assert "Failed to parse JSON" in captured.err
    assert reg.read_text(encoding="utf-8") == "{ bad json }"
