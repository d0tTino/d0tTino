import tomllib
from pathlib import Path

def test_starship_time_and_git_status_sections():
    data = tomllib.loads(Path('starship.toml').read_text())
    assert 'time' in data, '[time] section missing'
    assert 'git_status' in data, '[git_status] section missing'
    assert 'git_branch' in data, '[git_branch] section missing'
    assert 'git_state' in data, '[git_state] section missing'

def test_starship_multiline_format():
    data = tomllib.loads(Path('starship.toml').read_text())
    expected = "$directory$git_branch$git_state$git_status$fill$time\n$character"
    assert data.get('format') == expected, 'prompt format mismatch'

