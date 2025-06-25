import os
import shutil
import subprocess
from pathlib import Path


def create_stub_pwsh(path: Path) -> None:
    path.write_text(
        """#!/usr/bin/env bash
while [[ $# -gt 0 ]]; do
  if [[ $1 == -File ]]; then
    script=$2
    shift 2
  else
    shift
  fi
done
root=$(dirname "$script")
/bin/bash "$root/scripts/setup-hooks.sh"
""",
        encoding="utf-8",
    )
    path.chmod(0o755)


def test_bootstrap_sets_hooks_path(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy(repo_root / "bootstrap.ps1", repo / "bootstrap.ps1")
    shutil.copytree(repo_root / "scripts", repo / "scripts")

    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    stub_pwsh = stub_dir / "pwsh"
    create_stub_pwsh(stub_pwsh)

    env = os.environ.copy()
    env["PATH"] = f"{stub_dir}:{env['PATH']}"

    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(
        ["pwsh", "-NoLogo", "-NoProfile", "-File", str(repo / "bootstrap.ps1")],
        cwd=repo,
        env=env,
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
