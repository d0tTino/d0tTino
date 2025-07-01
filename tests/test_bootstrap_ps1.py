import os
import shutil
import subprocess
from pathlib import Path


def create_stub_pwsh(path: Path, log: Path | None = None) -> None:
    if log is None:
        log = path.parent / "pwsh.log"
    path.write_text(
        f"""#!/usr/bin/env bash
log_file='{log}'
file=""
args=()
while [[ $# -gt 0 ]]; do
  if [[ $1 == -File ]]; then
    file=$2
    shift 2
  else
    args+=($1)
    shift
  fi
done
root=$(dirname "$file")
base=$(basename "$file")
if [[ $base == bootstrap.ps1 ]]; then
  install_winget=false
  install_windows_terminal=false
  install_wsl=false
  setup_wsl=false
  setup_docker=false
  for arg in "${{args[@]}}"; do
    case $arg in
      -InstallWinget) install_winget=true ;;
      -InstallWindowsTerminal) install_windows_terminal=true ;;
      -InstallWSL) install_wsl=true ;;
      -SetupWSL) setup_wsl=true ;;
      -SetupDocker) setup_docker=true ;;
    esac
  done
  echo fix-path.ps1 >> "$log_file"
  echo setup-hooks.ps1 >> "$log_file"
  if [[ -f "$root/scripts/setup-hooks.sh" ]]; then
    /bin/bash "$root/scripts/setup-hooks.sh"
  fi
  $install_winget && echo setup-winget.ps1 >> "$log_file"
  $install_windows_terminal && echo install-windows-terminal.ps1 >> "$log_file"
  $install_wsl && echo install-wsl.ps1 >> "$log_file"
  $setup_wsl && echo setup-wsl.ps1 >> "$log_file"
  $setup_docker && echo setup-docker.ps1 >> "$log_file"
  exit 0
else
  echo "$base" >> "$log_file"
  exit 0
fi
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
        assert "setup-hooks.ps1" in lines
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
