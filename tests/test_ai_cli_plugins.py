import contextlib
import io

import pytest

pytest.importorskip("requests")

from scripts import ai_cli


def test_plugin_list_delegates(monkeypatch):
    called = {}

    def fake_main(argv):
        called['argv'] = argv
        return 0

    monkeypatch.setattr(ai_cli.plugins, 'main', fake_main)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(['plugin', 'backends', 'list'])
    assert rc == 0
    assert called['argv'] == ['backends', 'list']


def test_plugin_install_delegates(monkeypatch):
    called = {}
    def fake_main(argv):
        called['argv'] = argv
        return 0
    monkeypatch.setattr(ai_cli.plugins, 'main', fake_main)
    rc = ai_cli.main(['plugin', 'backends', 'install', 'x'])
    assert rc == 0
    assert called['argv'] == ['backends', 'install', 'x']


def test_plugin_remove_delegates(monkeypatch):
    called = {}
    def fake_main(argv):
        called['argv'] = argv
        return 0
    monkeypatch.setattr(ai_cli.plugins, 'main', fake_main)
    rc = ai_cli.main(['plugin', 'backends', 'remove', 'x'])
    assert rc == 0
    assert called['argv'] == ['backends', 'remove', 'x']
