import tomllib
from pathlib import Path


def test_starship_time_and_git_status_sections():
    data = tomllib.loads(Path('starship.toml').read_text())
    assert 'time' in data, '[time] section missing'
    assert 'git_status' in data, '[git_status] section missing'


def test_starship_format_contains_time_and_fill():
    data = tomllib.loads(Path('starship.toml').read_text())
    format_str = data.get('format', '')
    assert '$time' in format_str, 'format missing $time'
    assert '$fill' in format_str, 'format missing $fill'

