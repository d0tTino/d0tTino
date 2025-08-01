import os
import sys
import subprocess
import shutil
from pathlib import Path

import pytest
from tests.stubs import create_stub_pwsh

REPO_ROOT = Path(__file__).resolve().parents[1]

def _os_marker() -> str:
    if sys.platform.startswith("linux"):
        return "ubuntu-latest"
    if sys.platform == "darwin":
        return "macos-latest"
    return "windows-latest"

def test_install_sh_dry_run(tmp_path: Path) -> None:
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    create_stub_pwsh(stub_dir / "pwsh")

    env = os.environ.copy()
    env["PATH"] = f"{stub_dir}:{env['PATH']}"

    result = subprocess.run(
        ["bash", "install.sh", "--dry-run"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    output = result.stdout.strip().replace(str(REPO_ROOT) + "/", "")
    expected_path = REPO_ROOT / "tests" / "expected" / f"install_dry_run_{_os_marker()}.txt"
    assert output == expected_path.read_text().strip()


@pytest.mark.skipif(sys.platform != "win32", reason="requires Windows")
def test_bootstrap_ps1_dry_run() -> None:
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    assert pwsh is not None
    result = subprocess.run(
        [pwsh, "-NoLogo", "-NoProfile", "-File", str(REPO_ROOT / "bootstrap.ps1"), "-DryRun"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (result.stderr or result.stdout).strip()
    expected = (REPO_ROOT / "tests" / "expected" / "bootstrap_dry_run_windows-latest.txt").read_text().strip()
    assert expected in output
