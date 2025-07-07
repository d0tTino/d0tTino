import os
import shutil
import subprocess
from pathlib import Path


def create_exe(path: Path, contents: str = "#!/usr/bin/env bash\n") -> None:
    path.write_text(contents)
    path.chmod(0o755)


def test_install_sh_creates_hooks_and_palettes(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy(repo_root / "install.sh", repo / "install.sh")
    shutil.copytree(repo_root / "scripts", repo / "scripts")
    shutil.copytree(repo_root / ".githooks", repo / ".githooks")
    shutil.copytree(repo_root / "palettes", repo / "palettes")

    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["/bin/bash", "install.sh"], cwd=repo, check=True)

    result = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == ".githooks"
    assert (repo / "palettes" / "blacklight.toml").is_file()


def test_install_sh_runs_without_ostype(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo_no_ostype"
    repo.mkdir()
    shutil.copy(repo_root / "install.sh", repo / "install.sh")
    shutil.copytree(repo_root / "scripts", repo / "scripts")
    shutil.copytree(repo_root / ".githooks", repo / ".githooks")
    shutil.copytree(repo_root / "palettes", repo / "palettes")

    subprocess.run(["git", "init"], cwd=repo, check=True)
    env = os.environ.copy()
    env.pop("OSTYPE", None)
    subprocess.run(["/bin/bash", "install.sh"], cwd=repo, check=True, env=env)

    assert (repo / "palettes" / "blacklight.toml").is_file()


def test_install_sh_installs_nerd_font_macos(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo_macos"
    repo.mkdir()
    shutil.copy(repo_root / "install.sh", repo / "install.sh")
    shutil.copytree(repo_root / "scripts", repo / "scripts")
    shutil.copytree(repo_root / ".githooks", repo / ".githooks")
    shutil.copytree(repo_root / "palettes", repo / "palettes")

    subprocess.run(["git", "init"], cwd=repo, check=True)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    brew_log = tmp_path / "brew.log"
    create_exe(
        bin_dir / "brew",
        (
            "#!/usr/bin/env bash\n"
            f"echo \"$@\" >> '{brew_log}'\n"
            "if [[ $1 == list ]]; then exit 1; fi\n"
        ),
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["OSTYPE"] = "darwin"
    subprocess.run(["/bin/bash", "install.sh"], cwd=repo, check=True, env=env)

    lines = brew_log.read_text().splitlines()
    assert any("tap" in line for line in lines)
    assert any("font-caskaydia-cove-nerd-font" in line for line in lines)
