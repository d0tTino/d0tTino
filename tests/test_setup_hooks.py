import shutil
import subprocess
from pathlib import Path
import pytest


@pytest.mark.skipif(
    shutil.which("pwsh") is None and shutil.which("powershell") is None,
    reason="requires PowerShell",
)
def test_setup_hooks_ps1_sets_core_hooks_path(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    shutil.copytree(repo_root / "scripts", repo / "scripts")
    subprocess.run(["git", "init"], cwd=repo, check=True)
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    subprocess.run(
        [pwsh, "-NoLogo", "-NoProfile", "-File", "scripts/setup-hooks.ps1"],
        cwd=repo,
        check=True,
    )
    result = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == ".githooks"


def test_setup_hooks_sh_sets_core_hooks_path(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    shutil.copytree(repo_root / "scripts", repo / "scripts")
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["bash", "scripts/setup-hooks.sh"], cwd=repo, check=True)
    result = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == ".githooks"
