import json
from pathlib import Path


def load_json(path: Path):
    text = path.read_text()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        lines = [line.split("//", 1)[0] for line in text.splitlines()]
        cleaned = "\n".join(lines)
        return json.loads(cleaned)


def test_windows_terminal_settings():
    data = load_json(Path('windows-terminal') / 'settings.json')
    assert 'profiles' in data


def test_tablet_windows_terminal():
    data = load_json(Path('tablet-config/windows-terminal') / 'settings.json')
    assert '$schema' in data
