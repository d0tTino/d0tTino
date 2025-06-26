try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib
from pathlib import Path

def test_starship_time_and_git_status_sections():
    data = tomllib.loads(Path('starship.toml').read_text())
    assert 'time' in data, '[time] section missing'
    assert 'git_status' in data, '[git_status] section missing'
    assert data['git_status'].get('stashed') == "📦", 'stashed icon mismatch'
    assert 'git_branch' in data, '[git_branch] section missing'
    assert 'git_state' in data, '[git_state] section missing'
    assert 'status' in data, '[status] section missing'
    assert data['status'].get('disabled') is False, '[status] should be enabled'

    assert 'directory' in data, '[directory] section missing'
    assert data['directory'].get('style') == 'fg:blue', 'directory style mismatch'
    assert data['git_branch'].get('style') == 'fg:purple', 'git_branch style mismatch'
    assert data['git_status'].get('style') == 'fg:red', 'git_status style mismatch'
    assert data['time'].get('style') == 'fg:yellow', 'time style mismatch'

def test_starship_multiline_format():
    data = tomllib.loads(Path('starship.toml').read_text())
    expected = "[┌─](bold purple)$directory$git_branch$git_state$git_status$status$fill$time\n[└─](bold purple)$character\n"
    assert data.get('format') == expected, 'prompt format mismatch'
    assert data.get('add_newline') is False, 'add_newline should be false'

def test_starship_palette():
    data = tomllib.loads(Path('starship.toml').read_text())
    assert data.get('palette') == 'blacklight', 'palette not set to blacklight'
    palette = data.get('palettes', {}).get('blacklight', {})
    expected_colors = {
        'black': '#282c34',
        'red': '#e06c75',
        'green': '#98c379',
        'yellow': '#e5c07b',
        'blue': '#61afef',
        'purple': '#c678dd',
        'cyan': '#56b6c2',
        'white': '#dcdfe4',
        'bright_black': '#282c34',
        'bright_red': '#e06c75',
        'bright_green': '#98c379',
        'bright_yellow': '#e5c07b',
        'bright_blue': '#61afef',
        'bright_purple': '#c678dd',
        'bright_cyan': '#56b6c2',
        'bright_white': '#dcdfe4',
    }
    for name, value in expected_colors.items():
        assert palette.get(name) == value, f'{name} color mismatch'

