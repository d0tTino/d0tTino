import os
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_stub_stow(path: Path) -> None:
    path.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$*" >> "${STOW_LOG}"
"""
    )
    path.chmod(0o755)


def _setup_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()

    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    shutil.copy(REPO_ROOT / "scripts" / "install_dotfiles.sh", scripts_dir / "install_dotfiles.sh")

    for pkg in ("shell", "nvim", "tmux", "terminal", "btm"):
        (repo / "dotfiles" / pkg).mkdir(parents=True)

    (repo / "hosts" / "desktop").mkdir(parents=True)
    return repo


def test_install_dotfiles_requires_stow(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    shutil.copy(REPO_ROOT / "scripts" / "install_dotfiles.sh", scripts_dir / "install_dotfiles.sh")

    env = {"PATH": str(tmp_path / "bin")}
    (tmp_path / "bin").mkdir()

    result = subprocess.run(
        ["/bin/bash", "scripts/install_dotfiles.sh"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "GNU Stow is required" in result.stderr


def test_install_dotfiles_defaults_to_core_packages(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    stow_log = tmp_path / "stow.log"

    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    _write_stub_stow(stub_dir / "stow")

    env = os.environ.copy()
    env["PATH"] = f"{stub_dir}:{env['PATH']}"
    env["STOW_LOG"] = str(stow_log)

    subprocess.run(
        ["/bin/bash", "scripts/install_dotfiles.sh", "--dry-run"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    calls = stow_log.read_text().strip().splitlines()
    package_calls = [line.rsplit(" ", 1)[-1] for line in calls if line]
    assert package_calls == [
        "shell",
        "shell",
        "nvim",
        "nvim",
        "tmux",
        "tmux",
        "terminal",
        "terminal",
    ]


def test_install_dotfiles_selective_packages_and_host_order(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    stow_log = tmp_path / "stow.log"

    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    _write_stub_stow(stub_dir / "stow")

    env = os.environ.copy()
    env["PATH"] = f"{stub_dir}:{env['PATH']}"
    env["STOW_LOG"] = str(stow_log)

    subprocess.run(
        [
            "/bin/bash",
            "scripts/install_dotfiles.sh",
            "--dry-run",
            "--packages",
            "tmux,shell",
            "--host",
            "desktop",
        ],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    calls = stow_log.read_text().strip().splitlines()
    package_calls = [line.rsplit(" ", 1)[-1] for line in calls if line]
    assert package_calls == ["tmux", "tmux", "shell", "shell", "desktop", "desktop"]
