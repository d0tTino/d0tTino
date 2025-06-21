import pathlib

SCRIPT_PATH = pathlib.Path('scripts/setup-wsl.sh')


def test_starship_install_fallback():
    text = SCRIPT_PATH.read_text(encoding='utf-8')
    assert 'command -v starship' in text
    assert 'starship.rs/install.sh' in text


def test_zoxide_install_fallback():
    text = SCRIPT_PATH.read_text(encoding='utf-8')
    assert 'command -v zoxide' in text
    assert 'cargo install --locked zoxide' in text or 'zoxide/main/install.sh' in text
