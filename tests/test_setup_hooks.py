import os
import shutil
import subprocess
from pathlib import Path
import pytest


def create_fake_git(dir: Path, real_git: str, state_file: Path) -> None:
    script = dir / "git"
    script.write_text(
        f"""#!/usr/bin/env bash
real_git='{real_git}'
state_file='{state_file}'
if [[ "$1" == "config" && "$2" == "core.hooksPath" && "$3" == ".githooks" ]]; then
  "$real_git" "$@"
  echo set > "$state_file"
elif [[ "$1" == "config" && "$2" == "--get" && "$3" == "core.hooksPath" && -f "$state_file" ]]; then
  echo 'not.githooks'
else
  "$real_git" "$@"
fi
"""
    )
    script.chmod(0o755)


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


@pytest.mark.skipif(shutil.which("bash") is None, reason="requires bash")
def test_setup_hooks_sh_verification_failure(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    shutil.copytree(repo_root / "scripts", repo / "scripts")
    subprocess.run(["git", "init"], cwd=repo, check=True)
    real_git = shutil.which("git")
    bin_dir = repo / "bin"
    bin_dir.mkdir()
    state_file = repo / "state"
    create_fake_git(bin_dir, real_git, state_file)
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    result = subprocess.run(
        ["bash", "scripts/setup-hooks.sh"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "core.hooksPath" in result.stderr


@pytest.mark.skipif(
    shutil.which("pwsh") is None and shutil.which("powershell") is None,
    reason="requires PowerShell",
)
def test_setup_hooks_ps1_verification_failure(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    shutil.copytree(repo_root / "scripts", repo / "scripts")
    subprocess.run(["git", "init"], cwd=repo, check=True)
    real_git = shutil.which("git")
    bin_dir = repo / "bin"
    bin_dir.mkdir()
    state_file = repo / "state"
    create_fake_git(bin_dir, real_git, state_file)
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    result = subprocess.run(
        [pwsh, "-NoLogo", "-NoProfile", "-File", "scripts/setup-hooks.ps1"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "core.hooksPath" in result.stderr
