import json
from pathlib import Path
import json5


def load_json(path: Path):
    text = path.read_text()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json5.loads(text)


def test_windows_terminal_settings():
    data = load_json(Path('windows-terminal') / 'settings.json')
    assert 'profiles' in data
    profiles = data['profiles'].get('list', [])
    assert len(profiles) > 0, "no profiles configured"
    assert 'actions' in data and data['actions'], "action bindings missing"


def test_tablet_windows_terminal():
    data = load_json(Path('tablet-config/windows-terminal') / 'settings.json')
    assert '$schema' in data


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
