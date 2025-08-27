import io
import json
import types
import sys

from plugins import mcp, mcp_adapter


def test_mcp_adapter_exposes_registry_tools(monkeypatch):
    reg = {
        "dummy": {
            "package": "pkg",
            "mcp": {
                "server_url": "https://example.com",
                "capabilities": ["echo"],
            },
        }
    }
    monkeypatch.setattr(mcp_adapter.registry, "load_registry", lambda raw=True: reg)

    tools = mcp_adapter.get_tools(reg)
    assert tools["dummy"]() == {
        "server_url": "https://example.com",
        "capabilities": ["echo"],
    }


def test_mcp_adapter_tool_descriptors(monkeypatch):
    reg = {
        "dummy": {
            "package": "pkg",
            "mcp": {
                "server_url": "https://example.com",
                "capabilities": ["echo"],
            },
        }
    }
    monkeypatch.setattr(mcp_adapter.registry, "load_registry", lambda raw=True: reg)

    desc = mcp_adapter.get_tool_descriptors(reg)
    assert desc["dummy"] == {
        "name": "dummy",
        "server_url": "https://example.com",
        "capabilities": ["echo"],
    }


def test_ai_cli_flag_enables_mcp(monkeypatch, tmp_path):
    import importlib

    # Provide a minimal NATS stub so ai_cli can import without dependency.
    nats_mod = types.ModuleType("nats")
    nats_aio = types.ModuleType("nats.aio")
    nats_client = types.ModuleType("nats.aio.client")
    class Client:  # pragma: no cover - simple stub
        ...
    nats_client.Client = Client
    nats_aio.client = nats_client
    nats_mod.aio = nats_aio
    nats_js = types.ModuleType("nats.js")
    class JetStreamContext:  # pragma: no cover - simple stub
        ...
    nats_js.JetStreamContext = JetStreamContext
    monkeypatch.setitem(sys.modules, "nats", nats_mod)
    monkeypatch.setitem(sys.modules, "nats.aio", nats_aio)
    monkeypatch.setitem(sys.modules, "nats.aio.client", nats_client)
    monkeypatch.setitem(sys.modules, "nats.js", nats_js)

    ai_cli = importlib.import_module("scripts.ai_cli")

    monkeypatch.setattr(ai_cli, "SESSION_FILE", tmp_path / "session.json")
    monkeypatch.setattr(ai_cli.cli_actions, "record_event_logged", lambda *a, **k: None)

    called = {"value": False}

    def fake_get_tools():
        called["value"] = True
        return {}

    monkeypatch.setattr(mcp, "get_tools", fake_get_tools)

    ai_cli.main(["login", "user", "--enable-mcp"])
    assert called["value"]


def test_ai_cli_does_not_enable_mcp_without_flag(monkeypatch, tmp_path):
    import importlib

    nats_mod = types.ModuleType("nats")
    nats_aio = types.ModuleType("nats.aio")
    nats_client = types.ModuleType("nats.aio.client")
    class Client:  # pragma: no cover - simple stub
        ...
    nats_client.Client = Client
    nats_aio.client = nats_client
    nats_mod.aio = nats_aio
    nats_js = types.ModuleType("nats.js")
    class JetStreamContext:  # pragma: no cover - simple stub
        ...
    nats_js.JetStreamContext = JetStreamContext
    monkeypatch.setitem(sys.modules, "nats", nats_mod)
    monkeypatch.setitem(sys.modules, "nats.aio", nats_aio)
    monkeypatch.setitem(sys.modules, "nats.aio.client", nats_client)
    monkeypatch.setitem(sys.modules, "nats.js", nats_js)

    ai_cli = importlib.import_module("scripts.ai_cli")

    monkeypatch.setattr(ai_cli, "SESSION_FILE", tmp_path / "session.json")
    monkeypatch.setattr(ai_cli.cli_actions, "record_event_logged", lambda *a, **k: None)

    called = {"value": False}

    def fake_get_tools():
        called["value"] = True
        return {}

    monkeypatch.setattr(mcp, "get_tools", fake_get_tools)

    ai_cli.main(["login", "user"])
    assert not called["value"]


def test_mcp_adapter_serve_lists_descriptors(monkeypatch):
    reg = {
        "dummy": {
            "package": "pkg",
            "mcp": {
                "server_url": "https://example.com",
                "capabilities": ["echo"],
            },
        }
    }

    monkeypatch.setattr(mcp_adapter.sys, "stdin", io.StringIO(json.dumps({"command": "list_tools"}) + "\n"))
    stdout = io.StringIO()
    monkeypatch.setattr(mcp_adapter.sys, "stdout", stdout)

    mcp_adapter.serve(reg)
    resp = json.loads(stdout.getvalue())
    assert resp == {
        "result": [
            {
                "name": "dummy",
                "server_url": "https://example.com",
                "capabilities": ["echo"],
            }
        ]
    }

