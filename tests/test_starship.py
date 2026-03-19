from starship_expectations import (
    REQUIRED_MODULE_KEYS,
    REQUIRED_MODULE_VALUES,
    STARSHIP_PROMPT_FORMAT,
    load_starship,
)


def test_starship_time_and_git_status_sections():
    data = load_starship()
    for section, keys in REQUIRED_MODULE_KEYS.items():
        assert section in data, f'[{section}] section missing'
        for key in keys:
            assert key in data[section], f'{section}.{key} missing'
            assert data[section].get(key) == REQUIRED_MODULE_VALUES[section][key], (
                f'{section}.{key} mismatch'
            )


def test_starship_multiline_format():
    data = load_starship()
    assert data.get('format') == STARSHIP_PROMPT_FORMAT, 'prompt format mismatch'
    assert data.get('add_newline') is False, 'add_newline should be false'


def test_starship_python_indicator_is_minimal_and_contextual():
    data = load_starship()
    python = data['python']
    assert python['symbol'] == ' '
    assert python['style'] == 'fg:green'
    assert python['format'] == '[$symbol($virtualenv )($version)]($style) '
    assert '$virtualenv' in python['format']
    assert '$version' in python['format']
