import subprocess
import sys
from pathlib import Path


def test_generated_settings_up_to_date(tmp_path):
    script = Path('windows-terminal/generate_settings.py')
    base = Path('windows-terminal/settings.base.json')
    common = Path('windows-terminal/common-profiles.json')
    output = tmp_path / 'settings.json'
    subprocess.run([
        sys.executable,
        str(script),
        str(base),
        str(output),
        '--common',
        str(common),
    ], check=True)
    expected = Path('windows-terminal/settings.json').read_text(encoding='utf-8')
    generated = output.read_text(encoding='utf-8')
    assert generated == expected, (
        "windows-terminal/settings.json is out of date; run generate_settings.py"
    )
