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


def test_ai_cli_flag_enables_mcp(monkeypatch, tmp_path):
    import importlib

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
