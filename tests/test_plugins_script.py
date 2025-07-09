import sys
import pytest
from scripts import plugins


def test_list_outputs_available_plugins(monkeypatch, capsys):
    monkeypatch.setattr(plugins, "load_registry", lambda: {"dummy": "dummy-pkg"})
    monkeypatch.setattr(plugins, "_is_installed", lambda p: False)
    rc = plugins.main(["list"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert "dummy" in captured


def test_install_runs_pip(monkeypatch):
    called = {}
    def fake_run(cmd, *args, **kwargs):
        called["cmd"] = cmd
        called["kwargs"] = kwargs
        class Result:
            returncode = 0
        return Result()
    monkeypatch.setattr(plugins.subprocess, "run", fake_run)
    monkeypatch.setattr(plugins, "load_registry", lambda: {"dummy": "dummy-pkg"})
    rc = plugins.main(["install", "dummy"])
    assert rc == 0
    assert called["cmd"][0] == sys.executable
    assert "dummy-pkg" in called["cmd"]
    assert called["kwargs"].get("check")
    assert called["kwargs"].get("capture_output")
    assert called["kwargs"].get("text")


def test_remove_runs_pip(monkeypatch):
    called = {}

    def fake_run(cmd, *args, **kwargs):
        called["cmd"] = cmd
        called["kwargs"] = kwargs

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(plugins.subprocess, "run", fake_run)
    monkeypatch.setattr(plugins, "load_registry", lambda: {"dummy": "dummy-pkg"})
    rc = plugins.main(["remove", "dummy"])
    assert rc == 0
    assert called["cmd"][0] == sys.executable
    assert "dummy-pkg" in called["cmd"]
    assert called["kwargs"].get("check")
    assert called["kwargs"].get("capture_output")
    assert called["kwargs"].get("text")


def test_install_failure_propagates(monkeypatch, capsys):
    def fake_run(cmd, *args, **kwargs):
        raise plugins.subprocess.CalledProcessError(
            5, cmd, stderr="fail\n"
        )

    monkeypatch.setattr(plugins.subprocess, "run", fake_run)
    monkeypatch.setattr(plugins, "load_registry", lambda: {"dummy": "dummy-pkg"})
    rc = plugins.main(["install", "dummy"])
    captured = capsys.readouterr()
    assert rc == 5
    assert "fail" in captured.err


def test_remove_failure_propagates(monkeypatch, capsys):
    def fake_run(cmd, *args, **kwargs):
        raise plugins.subprocess.CalledProcessError(3, cmd, stderr="boom\n")

    monkeypatch.setattr(plugins.subprocess, "run", fake_run)
    monkeypatch.setattr(plugins, "load_registry", lambda: {"dummy": "dummy-pkg"})
    rc = plugins.main(["remove", "dummy"])
    captured = capsys.readouterr()
    assert rc == 3
    assert "boom" in captured.err


@pytest.mark.parametrize("retcode", [0, 4])
def test_main_remove(monkeypatch, capsys, retcode):
    called = {}

    def fake_run(cmd, *args, **kwargs):
        called["cmd"] = cmd
        if retcode:
            raise plugins.subprocess.CalledProcessError(retcode, cmd, stderr="fail\n")

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(plugins.subprocess, "run", fake_run)
    monkeypatch.setattr(plugins, "load_registry", lambda: {"dummy": "dummy-pkg"})
    rc = plugins.main(["remove", "dummy"])
    captured = capsys.readouterr()
    assert called["cmd"][0] == sys.executable
    assert "dummy-pkg" in called["cmd"]
    assert rc == retcode
    if retcode:
        assert "fail" in captured.err


def test_main_warns_when_jsonschema_missing(monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "jsonschema", None)
    import importlib
    reloaded = importlib.reload(plugins)
    monkeypatch.setattr(reloaded, "load_registry", lambda: {"dummy": "pkg"})
    monkeypatch.setattr(reloaded, "_is_installed", lambda p: False)
    rc = reloaded.main(["list"])
    out = capsys.readouterr()
    assert rc == 0
    assert "jsonschema is required" in out.err

