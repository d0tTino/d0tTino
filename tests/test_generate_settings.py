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


def test_generate_settings_invalid_json(tmp_path: Path) -> None:
    script = Path("windows-terminal/generate_settings.py")
    bad_base = tmp_path / "bad.json"
    bad_base.write_text("{ invalid json", encoding="utf-8")
    output = tmp_path / "out.json"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            str(bad_base),
            str(output),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert f"Failed to parse JSON from {bad_base}" in result.stderr

