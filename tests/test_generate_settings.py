import subprocess
import sys
from pathlib import Path
import importlib.util


def _load_generate_settings():
    spec = importlib.util.spec_from_file_location(
        "generate_settings", Path("windows-terminal/generate_settings.py")
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


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


def test_merge_profiles_duplicate_guid() -> None:
    module = _load_generate_settings()
    common = {
        "defaults": {"a": 1},
        "list": [
            {"guid": "{1111}", "name": "base", "color": "blue"},
            {"guid": "{1111}", "name": "base-dup"},
            {"name": "base-no-guid"},
        ],
    }
    override = {
        "defaults": {"b": 2},
        "list": [
            {"guid": "{1111}", "name": "override"},
            {"name": "override-no-guid"},
        ],
    }

    result = module.merge_profiles(common, override)

    assert result["defaults"] == {"a": 1, "b": 2}
    assert result["list"] == [
        {"guid": "{1111}", "name": "override", "color": "blue"},
        {"guid": "{1111}", "name": "base-dup"},
        {"name": "base-no-guid"},
        {"name": "override-no-guid"},
    ]


def test_merge_profiles_override_duplicates() -> None:
    module = _load_generate_settings()
    common = {
        "defaults": {},
        "list": [
            {"guid": "{2222}", "name": "base"},
        ],
    }
    override = {
        "defaults": {},
        "list": [
            {"guid": "{2222}", "name": "first"},
            {"guid": "{2222}", "name": "second"},
            {"name": "no-guid"},
        ],
    }

    result = module.merge_profiles(common, override)

    assert result["list"] == [
        {"guid": "{2222}", "name": "second"},
        {"name": "no-guid"},
    ]

