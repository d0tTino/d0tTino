import sys
from scripts import plugins


def test_list_outputs_available_plugins(monkeypatch, capsys):
    monkeypatch.setattr(plugins, "PLUGIN_REGISTRY", {"dummy": "dummy-pkg"})
    monkeypatch.setattr(plugins, "_is_installed", lambda p: False)
    rc = plugins.main(["list"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert "dummy" in captured


def test_install_runs_pip(monkeypatch):
    called = {}
    def fake_run(cmd):
        called["cmd"] = cmd
        class Result:
            returncode = 0
        return Result()
    monkeypatch.setattr(plugins.subprocess, "run", fake_run)
    monkeypatch.setattr(plugins, "PLUGIN_REGISTRY", {"dummy": "dummy-pkg"})
    rc = plugins.main(["install", "dummy"])
    assert rc == 0
    assert called["cmd"][0] == sys.executable
    assert "dummy-pkg" in called["cmd"]

