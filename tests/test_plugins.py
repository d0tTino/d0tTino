import argparse
import sys

import pytest
from scripts import plugins


class DummyRun:
    def __init__(self, returncode=0):
        self.returncode = returncode


def _make_args(name="dummy") -> argparse.Namespace:
    return argparse.Namespace(name=name, update=False)


@pytest.mark.parametrize("func,section", [
    (plugins._cmd_install_backend, "plugins"),
    (plugins._cmd_install_recipes, "recipes"),
])
def test_install_success(monkeypatch, func, section):
    called = {}

    def fake_run(cmd, *a, **k):
        called["cmd"] = cmd
        called["kwargs"] = k
        return DummyRun()

    def fake_load(sec="plugins", update=False):
        return {"dummy": "dummy-pkg"} if sec == section else {}

    monkeypatch.setattr(plugins.subprocess, "run", fake_run)
    monkeypatch.setattr(plugins, "load_registry", fake_load)

    rc = func(_make_args())
    assert rc == 0
    assert called["cmd"][0] == sys.executable
    assert "dummy-pkg" in called["cmd"]
    assert called["kwargs"].get("check")
    assert called["kwargs"].get("capture_output")
    assert called["kwargs"].get("text")


@pytest.mark.parametrize("func,section", [
    (plugins._cmd_remove_backend, "plugins"),
    (plugins._cmd_remove_recipes, "recipes"),
])
def test_remove_success(monkeypatch, func, section):
    called = {}

    def fake_run(cmd, *a, **k):
        called["cmd"] = cmd
        called["kwargs"] = k
        return DummyRun()

    def fake_load(sec="plugins", update=False):
        return {"dummy": "dummy-pkg"} if sec == section else {}

    monkeypatch.setattr(plugins.subprocess, "run", fake_run)
    monkeypatch.setattr(plugins, "load_registry", fake_load)

    rc = func(_make_args())
    assert rc == 0
    assert called["cmd"][0] == sys.executable
    assert "dummy-pkg" in called["cmd"]
    assert called["kwargs"].get("check")
    assert called["kwargs"].get("capture_output")
    assert called["kwargs"].get("text")


@pytest.mark.parametrize(
    "func,section",
    [
        (plugins._cmd_install_backend, "plugins"),
        (plugins._cmd_install_recipes, "recipes"),
    ],
)
def test_install_error(monkeypatch, capsys, func, section):
    def fake_run(cmd, *a, **k):
        raise plugins.subprocess.CalledProcessError(2, cmd, stderr="fail\n")

    def fake_load(sec="plugins", update=False):
        return {"dummy": "dummy-pkg"} if sec == section else {}

    monkeypatch.setattr(plugins.subprocess, "run", fake_run)
    monkeypatch.setattr(plugins, "load_registry", fake_load)

    rc = func(_make_args())
    captured = capsys.readouterr()
    assert rc == 2
    assert "fail" in captured.err


@pytest.mark.parametrize(
    "func,section",
    [
        (plugins._cmd_remove_backend, "plugins"),
        (plugins._cmd_remove_recipes, "recipes"),
    ],
)
def test_remove_error(monkeypatch, capsys, func, section):
    def fake_run(cmd, *a, **k):
        raise plugins.subprocess.CalledProcessError(3, cmd, stderr="boom\n")

    def fake_load(sec="plugins", update=False):
        return {"dummy": "dummy-pkg"} if sec == section else {}

    monkeypatch.setattr(plugins.subprocess, "run", fake_run)
    monkeypatch.setattr(plugins, "load_registry", fake_load)

    rc = func(_make_args())
    captured = capsys.readouterr()
    assert rc == 3
    assert "boom" in captured.err
