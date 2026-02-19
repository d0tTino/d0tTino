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
if [[ "${STOW_CONFLICT_PACKAGES:-}" == *",${@: -1},"* ]] && [[ "$*" == *" -nv "* ]]; then
    printf 'WARNING! stowing %s would cause conflicts:\n' "${@: -1}" >&2
    printf '* existing target is neither a link nor a directory: %s\n' "${STOW_CONFLICT_PATH:-.zshrc}" >&2
fi
"""
    )
    path.chmod(0o755)


def _write_stub_rm(path: Path) -> None:
    path.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$*" >> "${RM_LOG}"
/bin/rm "$@"
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
    (repo / "hosts" / "work_laptop").mkdir(parents=True)
    return repo


def _build_env(tmp_path: Path, stow_log: Path, rm_log: Path | None = None) -> dict[str, str]:
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    _write_stub_stow(stub_dir / "stow")
    if rm_log is not None:
        _write_stub_rm(stub_dir / "rm")

    env = os.environ.copy()
    env["PATH"] = f"{stub_dir}:{env['PATH']}"
    env["STOW_LOG"] = str(stow_log)
    if rm_log is not None:
        env["RM_LOG"] = str(rm_log)
    return env


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
    env = _build_env(tmp_path, stow_log)

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
    env = _build_env(tmp_path, stow_log)

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


def test_install_dotfiles_accepts_existing_work_laptop_overlay(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    stow_log = tmp_path / "stow.log"
    env = _build_env(tmp_path, stow_log)

    subprocess.run(
        [
            "/bin/bash",
            "scripts/install_dotfiles.sh",
            "--dry-run",
            "--host",
            "work_laptop",
        ],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    calls = stow_log.read_text().strip().splitlines()
    package_calls = [line.rsplit(" ", 1)[-1] for line in calls if line]
    assert package_calls[-2:] == ["work_laptop", "work_laptop"]


def test_install_dotfiles_core_then_host_overlay_order(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    stow_log = tmp_path / "stow.log"
    env = _build_env(tmp_path, stow_log)

    subprocess.run(
        [
            "/bin/bash",
            "scripts/install_dotfiles.sh",
            "--dry-run",
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
    assert package_calls == [
        "shell",
        "shell",
        "nvim",
        "nvim",
        "tmux",
        "tmux",
        "terminal",
        "terminal",
        "desktop",
        "desktop",
    ]


def test_install_dotfiles_conflict_abort_is_non_destructive(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    stow_log = tmp_path / "stow.log"
    rm_log = tmp_path / "rm.log"
    env = _build_env(tmp_path, stow_log, rm_log)
    env["STOW_CONFLICT_PACKAGES"] = ",shell,"
    target = tmp_path / "target"
    target.mkdir()
    (target / ".zshrc").write_text("keep me")

    result = subprocess.run(
        ["/bin/bash", "scripts/install_dotfiles.sh", "--target", str(target), "--packages", "shell"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Aborting due to existing targets" in result.stderr
    assert (target / ".zshrc").read_text() == "keep me"
    assert not rm_log.exists() or rm_log.read_text().strip() == ""


def test_install_dotfiles_conflict_backup_moves_to_backup_path(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    stow_log = tmp_path / "stow.log"
    rm_log = tmp_path / "rm.log"
    env = _build_env(tmp_path, stow_log, rm_log)
    env["STOW_CONFLICT_PACKAGES"] = ",shell,"
    target = tmp_path / "target"
    target.mkdir()
    (target / ".zshrc").write_text("keep me")

    subprocess.run(
        [
            "/bin/bash",
            "scripts/install_dotfiles.sh",
            "--target",
            str(target),
            "--packages",
            "shell",
            "--conflict",
            "backup",
        ],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    backups = list((target / ".dotfiles-backups").glob("*/shell/.zshrc"))
    assert len(backups) == 1
    assert backups[0].read_text() == "keep me"
    assert not (target / ".zshrc").exists()
    assert not rm_log.exists() or rm_log.read_text().strip() == ""


def test_install_dotfiles_conflict_overwrite_deletes_conflict(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    stow_log = tmp_path / "stow.log"
    rm_log = tmp_path / "rm.log"
    env = _build_env(tmp_path, stow_log, rm_log)
    env["STOW_CONFLICT_PACKAGES"] = ",shell,"
    target = tmp_path / "target"
    target.mkdir()
    (target / ".zshrc").write_text("old")

    subprocess.run(
        [
            "/bin/bash",
            "scripts/install_dotfiles.sh",
            "--target",
            str(target),
            "--packages",
            "shell",
            "--conflict=overwrite",
        ],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    assert rm_log.read_text().strip() == "-rf {}".format(target / ".zshrc")
