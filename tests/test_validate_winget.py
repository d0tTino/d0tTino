import json  # noqa: F401
import subprocess
from pathlib import Path
import sys


def test_validate_winget_malformed(tmp_path: Path) -> None:
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{ invalid json }", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "scripts/validate_winget.py", str(bad_json)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Failed to parse" in result.stderr


def test_validate_winget_success(tmp_path: Path) -> None:
    valid_json = tmp_path / "good.json"
    valid_json.write_text(
        '{"Sources": [{"Packages": ["foo"]}]}',
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "scripts/validate_winget.py", str(valid_json)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

