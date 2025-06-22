import tomllib
from pathlib import Path


def test_starship_time_and_git_status_sections():
    data = tomllib.loads(Path('starship.toml').read_text())
    assert 'time' in data, '[time] section missing'
    assert 'git_status' in data, '[git_status] section missing'

