import importlib.metadata
import sys
import types

from plugins import mcp


def test_mcp_adapter_exposes_registered_tools(monkeypatch):
    module = types.ModuleType("dummy_tool_mod")

    def tool_func():
        return "ok"

    module.tool = tool_func
    monkeypatch.setitem(sys.modules, "dummy_tool_mod", module)

    entry = importlib.metadata.EntryPoint(
        name="dummy", value="dummy_tool_mod:tool", group="d0ttino.tools"
    )
    monkeypatch.setattr(mcp, "discover_entry_points", lambda group: iter([entry]))

    tools = mcp.get_tools()
    assert tools["dummy"] is tool_func


def test_ai_cli_flag_enables_mcp(monkeypatch, tmp_path):
    from scripts import ai_cli

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
    from scripts import ai_cli

    monkeypatch.setattr(ai_cli, "SESSION_FILE", tmp_path / "session.json")
    monkeypatch.setattr(ai_cli.cli_actions, "record_event_logged", lambda *a, **k: None)

    called = {"value": False}

    def fake_get_tools():
        called["value"] = True
        return {}

    monkeypatch.setattr(mcp, "get_tools", fake_get_tools)

    ai_cli.main(["login", "user"])
    assert not called["value"]
