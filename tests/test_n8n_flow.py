import json
from pathlib import Path


def test_mcp_node_present():
    data = json.loads(Path('n8n/flows/mcp-ai_exec.json').read_text())
    assert any(n.get('type') == 'n8n-nodes-mcp.mcpClient' for n in data['nodes'])

    conns = data.get('connections', {})
    start_main = conns.get('Start', {}).get('main', [])
    assert start_main and start_main[0][0]['node'] == 'mcp'
    mcp_main = conns.get('mcp', {}).get('main', [])
    assert mcp_main and mcp_main[0][0]['node'] == 'ai_exec'

