import os
import shutil
import subprocess
from pathlib import Path

from tests.stubs import create_stub_install, create_stub_install_common, create_stub_pwsh

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


def test_bootstrap_invokes_optional_scripts(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy(repo_root / "bootstrap.ps1", repo / "bootstrap.ps1")

    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    log_file = tmp_path / "pwsh.log"
    create_stub_pwsh(stub_dir / "pwsh", log_file)

    env = os.environ.copy()
    env.update({
        "PATH": f"{stub_dir}:{env['PATH']}",
        "PWSH_LOG": str(log_file),
    })

    flags = [
        ("-InstallWinget", "setup-winget.ps1"),
        ("-InstallWindowsTerminal", "install-windows-terminal.ps1"),
        ("-InstallWSL", "install-wsl.ps1"),
        ("-SetupWSL", "setup-wsl.ps1"),
    ]

    for flag, expected in flags:
        log_file.write_text("")
        subprocess.run(
            ["pwsh", "-NoLogo", "-NoProfile", "-File", str(repo / "bootstrap.ps1"), flag],
            cwd=repo,
            env=env,
            check=True,
        )
        lines = log_file.read_text().splitlines()
        assert "fix-path.ps1" in lines
        assert "install_common.sh" in lines
        assert expected in lines


def test_bootstrap_setup_docker(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy(repo_root / "bootstrap.ps1", repo / "bootstrap.ps1")

    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    log_file = tmp_path / "pwsh.log"
    create_stub_pwsh(stub_dir / "pwsh", log_file)

    env = os.environ.copy()
    env.update({
        "PATH": f"{stub_dir}:{env['PATH']}",
        "PWSH_LOG": str(log_file),
    })

    subprocess.run(
        [
            "pwsh",
            "-NoLogo",
            "-NoProfile",
            "-File",
            str(repo / "bootstrap.ps1"),
            "-SetupDocker",
            "-DockerImageName",
            "custom:latest",
        ],
        cwd=repo,
        env=env,
        check=True,
    )

    lines = log_file.read_text().splitlines()
    assert "setup-docker.ps1" in lines


def _prepare_repo(tmp_path: Path, name: str, log: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / name
    repo.mkdir()
    shutil.copy(repo_root / "bootstrap.ps1", repo / "bootstrap.ps1")
    shutil.copytree(repo_root / "scripts", repo / "scripts")
    create_stub_install(repo / "scripts" / "install.sh", log)
    create_stub_install_common(repo / "scripts" / "install_common.sh", log)
    return repo


def test_bootstrap_installs_fonts_macos(tmp_path: Path) -> None:
    log_file = tmp_path / "pwsh.log"
    repo = _prepare_repo(tmp_path, "repo_macos", log_file)

    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    create_stub_pwsh(stub_dir / "pwsh", log_file)

    env = os.environ.copy()
    env.update({"PATH": f"{stub_dir}:{env['PATH']}", "STUB_IS_WINDOWS": "0", "OSTYPE": "darwin"})

    subprocess.run(
        ["pwsh", "-NoLogo", "-NoProfile", "-File", str(repo / "bootstrap.ps1")],
        cwd=repo,
        env=env,
        check=True,
    )

    lines = log_file.read_text().splitlines()
    assert "install_common" in lines
    assert "install_fonts_unix" in lines
    assert "pull_palettes" in lines


def test_bootstrap_installs_fonts_windows(tmp_path: Path) -> None:
    log_file = tmp_path / "pwsh.log"
    repo = _prepare_repo(tmp_path, "repo_windows", log_file)

    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    create_stub_pwsh(stub_dir / "pwsh", log_file)

    env = os.environ.copy()
    env.update({"PATH": f"{stub_dir}:{env['PATH']}", "STUB_IS_WINDOWS": "1", "OSTYPE": "msys"})

    subprocess.run(
        ["pwsh", "-NoLogo", "-NoProfile", "-File", str(repo / "bootstrap.ps1")],
        cwd=repo,
        env=env,
        check=True,
    )

    lines = log_file.read_text().splitlines()
    assert "install_common" in lines
    assert "install_fonts_windows" in lines
    assert "pull_palettes" in lines
