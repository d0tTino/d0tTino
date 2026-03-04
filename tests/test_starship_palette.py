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
