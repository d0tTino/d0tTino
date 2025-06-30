import json
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


def test_validate_winget_no_packages(tmp_path: Path) -> None:
    json_file = tmp_path / "no_packages.json"
    json_file.write_text(
        json.dumps({"Sources": [{"Name": "TestSource"}]}, ensure_ascii=False),
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "scripts/validate_winget.py", str(json_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "has no packages" in result.stderr
