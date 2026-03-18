from starship_expectations import STARSHIP_PROMPT_FORMAT, expected_default_palette, load_starship

def test_blacklight_format_and_newline():
    data = load_starship()
    assert data.get('format') == STARSHIP_PROMPT_FORMAT, 'format string mismatch'
    assert data.get('add_newline') is False, 'add_newline should be false'

def test_default_palette_colors():
    data = load_starship()
    default_name, expected_colors = expected_default_palette()
    assert data.get('palette') == default_name, f'palette not set to {default_name}'
    palette = data.get('palettes', {}).get(default_name, {})
    for name, value in expected_colors.items():
        assert palette.get(name) == value, f'{name} color mismatch'



def test_default_palette_matches_terminal_defaults_and_nvim_artifacts():
    from pathlib import Path
    import re

    repo_root = Path(__file__).resolve().parents[1]
    defaults_text = (repo_root / "dotfiles" / "terminal" / ".config" / "tino" / "terminal-defaults.sh").read_text(encoding="utf-8")
    nvim_text = (repo_root / "dotfiles" / "nvim" / ".config" / "nvim" / "lua" / "config" / "palette.lua").read_text(encoding="utf-8")

    def exported(name: str) -> str:
        match = re.search(rf'^export {name}="([^"]+)"$', defaults_text, re.MULTILINE)
        assert match, f"missing export for {name}"
        return match.group(1)

    data = load_starship()
    palette = data["palettes"][data["palette"]]
    starship_to_terminal = {
        "black": "TINO_TERMINAL_COLOR_0",
        "red": "TINO_TERMINAL_COLOR_1",
        "green": "TINO_TERMINAL_COLOR_2",
        "yellow": "TINO_TERMINAL_COLOR_3",
        "blue": "TINO_TERMINAL_COLOR_4",
        "purple": "TINO_TERMINAL_COLOR_5",
        "cyan": "TINO_TERMINAL_COLOR_6",
        "white": "TINO_TERMINAL_COLOR_7",
        "bright_black": "TINO_TERMINAL_COLOR_8",
        "bright_red": "TINO_TERMINAL_COLOR_9",
        "bright_green": "TINO_TERMINAL_COLOR_10",
        "bright_yellow": "TINO_TERMINAL_COLOR_11",
        "bright_blue": "TINO_TERMINAL_COLOR_12",
        "bright_purple": "TINO_TERMINAL_COLOR_13",
        "bright_cyan": "TINO_TERMINAL_COLOR_14",
        "bright_white": "TINO_TERMINAL_COLOR_15",
    }
    for starship_key, terminal_var in starship_to_terminal.items():
        assert palette[starship_key] == exported(terminal_var)

    nvim_expectations = {
        "bg": exported("TINO_TERMINAL_BACKGROUND"),
        "fg": exported("TINO_TERMINAL_FOREGROUND"),
        "gray": exported("TINO_TERMINAL_COLOR_8"),
        "pink": exported("TINO_TERMINAL_COLOR_1"),
        "green": exported("TINO_TERMINAL_COLOR_2"),
        "yellow": exported("TINO_TERMINAL_COLOR_3"),
        "blue": exported("TINO_TERMINAL_COLOR_4"),
        "purple": exported("TINO_TERMINAL_COLOR_5"),
        "cyan": exported("TINO_TERMINAL_COLOR_6"),
        "magenta": exported("TINO_TERMINAL_COLOR_13"),
        "white": exported("TINO_TERMINAL_COLOR_15"),
    }
    for key, value in nvim_expectations.items():
        assert re.search(rf'{key}\s*=\s*"{re.escape(value)}"', nvim_text), f"nvim palette mismatch for {key}"
