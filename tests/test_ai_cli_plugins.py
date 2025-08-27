import contextlib
import io
import sys
import types

import pytest

pytest.importorskip("requests")

nats = types.ModuleType("nats")
aio = types.ModuleType("aio")
client = types.ModuleType("client")
js = types.ModuleType("js")
setattr(client, "Client", object)
setattr(js, "JetStreamContext", object)
aio.client = client
nats.js = js
nats.aio = aio
sys.modules.setdefault("nats", nats)
sys.modules.setdefault("nats.aio", aio)
sys.modules.setdefault("nats.aio.client", client)
sys.modules.setdefault("nats.js", js)

from scripts import ai_cli  # noqa: E402
from plugins import mcp_adapter  # noqa: E402


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


def test_plugin_mcp_enable_delegates(monkeypatch):
    called = {}

    def fake_main(argv):
        called['argv'] = argv
        return 0

    monkeypatch.setattr(ai_cli.plugins, 'main', fake_main)
    rc = ai_cli.main(['plugin', 'mcp', 'enable', 'x'])
    assert rc == 0
    assert called['argv'] == ['mcp', 'enable', 'x']


def test_mcp_subcommand_runs_server(monkeypatch):
    called = {'value': False}

    def fake_serve():
        called['value'] = True

    monkeypatch.setattr(mcp_adapter, 'serve', fake_serve)
    rc = ai_cli.main(['mcp'])
    assert rc == 0
    assert called['value']
