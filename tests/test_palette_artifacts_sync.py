from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_palette_artifacts_are_in_sync() -> None:
    subprocess.run(
        [sys.executable, "scripts/helpers/generate_palette_artifacts.py", "--check"],
        cwd=REPO_ROOT,
        check=True,
    )


def test_sync_palettes_script_executes() -> None:
    subprocess.run([
        "bash",
        "scripts/helpers/sync_palettes.sh",
    ], cwd=REPO_ROOT, check=True)
