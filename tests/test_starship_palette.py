try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib
from pathlib import Path


EXPECTED_FORMAT = (
    "[┌─](bold purple)$directory$git_branch$git_state$git_status$status$fill$time\n"
    "[└─](bold purple)$character\n"
)

EXPECTED_COLORS = {
    "black": "#000000",
    "red": "#ff66c4",
    "green": "#b2ff59",
    "yellow": "#ffff66",
    "blue": "#66b2ff",
    "purple": "#845CFF",
    "cyan": "#66fff2",
    "white": "#f2f2f2",
    "bright_black": "#666666",
    "bright_red": "#ff66c4",
    "bright_green": "#b2ff59",
    "bright_yellow": "#ffff66",
    "bright_blue": "#66b2ff",
    "bright_purple": "#FC17DA",
    "bright_cyan": "#66fff2",
    "bright_white": "#ffffff",
}

def load_starship():
    return tomllib.loads(Path('starship.toml').read_text())

def test_blacklight_format_and_newline():
    data = load_starship()
    assert data.get('format') == EXPECTED_FORMAT, 'format string mismatch'
    assert data.get('add_newline') is False, 'add_newline should be false'

def test_blacklight_palette_colors():
    data = load_starship()
    assert data.get('palette') == 'blacklight', 'palette not set to blacklight'
    palette = data.get('palettes', {}).get('blacklight', {})
    for name, value in EXPECTED_COLORS.items():
        assert palette.get(name) == value, f'{name} color mismatch'

