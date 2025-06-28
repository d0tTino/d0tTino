from test_starship_palette import EXPECTED_COLORS, load_starship

def test_starship_time_and_git_status_sections():
    data = load_starship()
    assert 'time' in data, '[time] section missing'
    assert 'git_status' in data, '[git_status] section missing'
    assert data['git_status'].get('stashed') == "📦", 'stashed icon mismatch'
    assert 'git_branch' in data, '[git_branch] section missing'
    assert 'git_state' in data, '[git_state] section missing'
    assert 'status' in data, '[status] section missing'
    assert data['status'].get('disabled') is False, '[status] should be enabled'

    assert 'directory' in data, '[directory] section missing'
    assert data['directory'].get('style') == 'fg:bright_purple', 'directory style mismatch'
    assert data['git_branch'].get('style') == 'fg:purple', 'git_branch style mismatch'
    assert data['git_status'].get('style') == 'fg:bright_purple', 'git_status style mismatch'
    assert data['time'].get('style') == 'fg:purple', 'time style mismatch'

def test_starship_multiline_format():
    data = load_starship()
    expected = "[┌─](bold purple)$directory$git_branch$git_state$git_status$status$fill$time\n[└─](bold purple)$character\n"
    assert data.get('format') == expected, 'prompt format mismatch'
    assert data.get('add_newline') is False, 'add_newline should be false'

def test_starship_palette():
    data = load_starship()
    assert data.get('palette') == 'blacklight', 'palette not set to blacklight'
    palette = data.get('palettes', {}).get('blacklight', {})
    expected_colors = {
        'black': '#000000',
        'red': '#ff66c4',
        'green': '#b2ff59',
        'yellow': '#ffff66',
        'blue': '#66b2ff',
        'purple': '#845CFF',
        'cyan': '#66fff2',
        'white': '#f2f2f2',
        'bright_black': '#666666',
        'bright_red': '#ff66c4',
        'bright_green': '#b2ff59',
        'bright_yellow': '#ffff66',
        'bright_blue': '#66b2ff',
        'bright_purple': '#FC17DA',
        'bright_cyan': '#66fff2',
        'bright_white': '#ffffff',
    }
    for name, value in expected_colors.items():

        assert palette.get(name) == value, f'{name} color mismatch'

