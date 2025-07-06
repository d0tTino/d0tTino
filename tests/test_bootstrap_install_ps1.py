import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(
    shutil.which("pwsh") is None and shutil.which("powershell") is None,
    reason="requires PowerShell",
)
def test_bootstrap_ps1_creates_hooks_and_palettes(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy(repo_root / "bootstrap.ps1", repo / "bootstrap.ps1")
    shutil.copytree(repo_root / "scripts", repo / "scripts")
    shutil.copytree(repo_root / ".githooks", repo / ".githooks")
    shutil.copytree(repo_root / "palettes", repo / "palettes")

    subprocess.run(["git", "init"], cwd=repo, check=True)

    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    subprocess.run([pwsh, "-NoLogo", "-NoProfile", "-File", str(repo / "bootstrap.ps1")], cwd=repo, check=True)

    result = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == ".githooks"
    assert (repo / "palettes" / "blacklight.toml").is_file()
