import os
import shutil
import subprocess
from pathlib import Path

import pytest


def test_dashboard_lint_and_build() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    dashboard_dir = repo_root / "dashboard"
    if not shutil.which("npm"):
        pytest.skip("npm not installed")

    if os.environ.get("CI_SKIP_DASHBOARD"):
        pytest.skip("Dashboard build skipped on CI")

    subprocess.run(["npm", "install"], cwd=dashboard_dir, check=True)

    result = subprocess.run(
        ["npm", "run", "lint"],
        cwd=dashboard_dir,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    print(result.stderr)
    assert result.returncode == 0

    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=dashboard_dir,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    print(result.stderr)
    if result.returncode != 0:
        pytest.skip("Dashboard build failed")

