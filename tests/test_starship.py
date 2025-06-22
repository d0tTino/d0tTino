from pathlib import Path


def test_starship_has_time_and_git_status():
    text = Path('starship.toml').read_text(encoding='utf-8')
    assert '[time]' in text
    assert '[git_status]' in text
