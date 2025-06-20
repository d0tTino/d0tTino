import json
from pathlib import Path


def load_json(path: Path):
    with path.open() as f:
        return json.load(f)


def test_oh_my_posh_theme():
    data = load_json(Path('oh-my-posh') / 'theme.omp.json')
    assert 'schemaVersion' in data


def test_windows_terminal_settings():
    data = load_json(Path('windows-terminal') / 'settings.json')
    assert 'profiles' in data


def test_tablet_custom_tokyo():
    data = load_json(Path('tablet-config/oh-my-posh') / 'custom_tokyo.omp.json')
    assert '$schema' in data


def test_tablet_windows_terminal():
    data = load_json(Path('tablet-config/windows-terminal') / 'settings.json')
    assert '$schema' in data
