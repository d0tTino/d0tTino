import subprocess
import sys
from pathlib import Path


def test_list_palettes_outputs_available_palettes(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "thm.py"
    result = subprocess.run(
        [sys.executable, str(script), "list-palettes"],
        capture_output=True,
        text=True,
        check=True,
    )
    output = result.stdout.strip().splitlines()
    assert "blacklight" in output
