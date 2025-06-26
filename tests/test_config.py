import json
from pathlib import Path
import pytest

json5 = pytest.importorskip("json5")


def load_json(path: Path):
    text = path.read_text()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json5.loads(text)


def find_binding(actions: list[dict], key: str) -> dict | None:
    """Return the binding dict matching ``key`` if present."""
    for action in actions:
        if action.get("keys") == key:
            return action
    return None


def test_windows_terminal_settings():
    data = load_json(Path('windows-terminal') / 'settings.json')
    assert data.get('defaultProfile'), 'default profile missing'
    assert data['defaultProfile'] == '{1857054d-df21-5f4a-bd44-865a14a14d59}'
    assert 'profiles' in data
    profiles = data['profiles'].get('list', [])
    assert len(profiles) > 0, "no profiles configured"
    defaults = data['profiles'].get('defaults', {})
    assert defaults.get('useAcrylic') is True, 'acrylic not enabled'
    assert 'acrylicOpacity' in defaults, 'acrylic opacity missing'
    assert defaults.get('acrylicOpacity') == 0.85
    color = defaults.get('colorScheme')
    if not color:
        for p in profiles:
            if 'colorScheme' in p:
                color = p['colorScheme']
                break
    assert color, 'color scheme missing'
    assert 'actions' in data and data['actions'], "action bindings missing"


def test_windows_terminal_split_bindings():
    """The starter settings should bind Alt+V and Alt+H for pane splitting."""
    data = load_json(Path('windows-terminal') / 'settings.json')
    actions = data.get('actions', [])

    binding_v = find_binding(actions, 'alt+v')
    assert binding_v, 'Alt+V binding missing'
    assert binding_v.get('command', {}).get('action') == 'splitPane'
    assert binding_v.get('command', {}).get('split') == 'vertical'
    assert binding_v.get('command', {}).get('profile') == '{1857054d-df21-5f4a-bd44-865a14a14d59}'

    binding_h = find_binding(actions, 'alt+h')
    assert binding_h, 'Alt+H binding missing'
    assert binding_h.get('command', {}).get('action') == 'splitPane'
    assert binding_h.get('command', {}).get('split') == 'horizontal'
    assert binding_h.get('command', {}).get('profile') == '{574e775e-4f2a-5b96-ac1e-a2962a402336}'

    binding_close = find_binding(actions, 'ctrl+shift+w')
    assert binding_close, 'Ctrl+Shift+W binding missing'
    assert binding_close.get('command', {}).get('action') == 'closePane'


def test_windows_terminal_btm_binding():
    """Alt+M should open btm in a new tab."""
    data = load_json(Path('windows-terminal') / 'settings.json')
    actions = data.get('actions', [])

    binding = find_binding(actions, 'alt+m')
    assert binding, 'Alt+M binding missing'
    cmd = binding.get('command', {})
    assert cmd.get('action') == 'newTab'
    assert cmd.get('commandline') == 'btm'



def test_tablet_windows_terminal():
    data = load_json(Path('tablet-config/windows-terminal') / 'settings.json')
    assert '$schema' in data
    assert 'profiles' in data
    assert 'actions' in data


def test_load_json5(tmp_path):
    json_with_comments = (
        '{\n'
        '  "url": "https://example.com", // comment after value\n'
        '  "answer": 42\n'
        '}'
    )
    file = tmp_path / "data.json"
    file.write_text(json_with_comments)
    data = load_json(file)
    assert data["url"] == "https://example.com"
    assert data["answer"] == 42
