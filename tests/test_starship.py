from starship_expectations import REQUIRED_MODULE_KEYS, STARSHIP_PROMPT_FORMAT, load_starship

def test_starship_time_and_git_status_sections():
    data = load_starship()
    for section, keys in REQUIRED_MODULE_KEYS.items():
        assert section in data, f'[{section}] section missing'
        for key in keys:
            assert key in data[section], f'{section}.{key} missing'

    assert data['git_status'].get('stashed') == "📦", 'stashed icon mismatch'
    assert data['status'].get('disabled') is False, '[status] should be enabled'

def test_starship_multiline_format():
    data = load_starship()
    assert data.get('format') == STARSHIP_PROMPT_FORMAT, 'prompt format mismatch'
    assert data.get('add_newline') is False, 'add_newline should be false'
