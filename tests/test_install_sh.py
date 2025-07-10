import os
import shutil
import subprocess
from pathlib import Path

from tests.stubs import create_stub_install, create_stub_install_common, create_stub_pwsh


def create_exe(path: Path, contents: str = "#!/usr/bin/env bash\n") -> None:
    path.write_text(contents, encoding="utf-8")
    path.chmod(0o755)

def test_install_sh_creates_hooks_and_palettes(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy(repo_root / "install.sh", repo / "install.sh")
    shutil.copytree(repo_root / "scripts", repo / "scripts")
    install_log = tmp_path / "install.log"
    create_stub_install(repo / "scripts" / "install.sh", install_log)
    create_stub_install_common(repo / "scripts" / "install_common.sh", install_log)
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
    lines = install_log.read_text().splitlines()
    assert "install_common" in lines
    assert "install_fonts_unix" in lines
    assert "pull_palettes" in lines


def test_install_sh_runs_without_ostype(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo_no_ostype"
    repo.mkdir()
    shutil.copy(repo_root / "install.sh", repo / "install.sh")
    shutil.copytree(repo_root / "scripts", repo / "scripts")
    install_log = tmp_path / "install_no_ostype.log"
    create_stub_install(repo / "scripts" / "install.sh", install_log)
    create_stub_install_common(repo / "scripts" / "install_common.sh", install_log)
    shutil.copytree(repo_root / ".githooks", repo / ".githooks")
    shutil.copytree(repo_root / "palettes", repo / "palettes")

    subprocess.run(["git", "init"], cwd=repo, check=True)
    env = os.environ.copy()
    env.pop("OSTYPE", None)
    subprocess.run(["/bin/bash", "install.sh"], cwd=repo, check=True, env=env)

    assert (repo / "palettes" / "blacklight.toml").is_file()
    lines = install_log.read_text().splitlines()
    assert "install_common" in lines
    assert "install_fonts_unix" in lines
    assert "pull_palettes" in lines


def test_install_sh_installs_nerd_font_macos(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo_macos"
    repo.mkdir()
    shutil.copy(repo_root / "install.sh", repo / "install.sh")
    shutil.copytree(repo_root / "scripts", repo / "scripts")
    install_log = tmp_path / "install_macos.log"
    create_stub_install(repo / "scripts" / "install.sh", install_log)
    create_stub_install_common(repo / "scripts" / "install_common.sh", install_log)
    shutil.copytree(repo_root / ".githooks", repo / ".githooks")
    shutil.copytree(repo_root / "palettes", repo / "palettes")

    subprocess.run(["git", "init"], cwd=repo, check=True)

    env = os.environ.copy()
    env["OSTYPE"] = "darwin"
    subprocess.run(["/bin/bash", "install.sh"], cwd=repo, check=True, env=env)

    lines = install_log.read_text().splitlines()
    assert "install_common" in lines
    assert "install_fonts_unix" in lines
    assert "pull_palettes" in lines


def test_install_sh_installs_nerd_font_windows(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo_windows"
    repo.mkdir()
    shutil.copy(repo_root / "install.sh", repo / "install.sh")
    shutil.copytree(repo_root / "scripts", repo / "scripts")
    install_log = tmp_path / "install_windows.log"
    create_stub_install(repo / "scripts" / "install.sh", install_log)
    create_stub_install_common(repo / "scripts" / "install_common.sh", install_log)

    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    create_stub_pwsh(stub_dir / "pwsh", install_log)

    shutil.copytree(repo_root / ".githooks", repo / ".githooks")
    shutil.copytree(repo_root / "palettes", repo / "palettes")

    subprocess.run(["git", "init"], cwd=repo, check=True)

    env = os.environ.copy()
    env["OSTYPE"] = "msys"
    env["PATH"] = f"{stub_dir}:{env['PATH']}"
    subprocess.run(["/bin/bash", "install.sh"], cwd=repo, check=True, env=env)

    lines = install_log.read_text().splitlines()
    assert "fix-path.ps1" in lines
    assert "install_common" in lines
    assert "install_fonts_windows" in lines
    assert "pull_palettes" in lines


def test_install_sh_installs_nerd_font_linux(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo_linux"
    repo.mkdir()
    shutil.copy(repo_root / "install.sh", repo / "install.sh")
    shutil.copytree(repo_root / "scripts", repo / "scripts")
    install_log = tmp_path / "install_linux.log"
    create_stub_install(repo / "scripts" / "install.sh", install_log)
    create_stub_install_common(repo / "scripts" / "install_common.sh", install_log)
    shutil.copytree(repo_root / ".githooks", repo / ".githooks")
    shutil.copytree(repo_root / "palettes", repo / "palettes")

    subprocess.run(["git", "init"], cwd=repo, check=True)

    env = os.environ.copy()
    env["OSTYPE"] = "linux-gnu"
    subprocess.run(["/bin/bash", "install.sh"], cwd=repo, check=True, env=env)

    result = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == ".githooks"
    assert (repo / "palettes" / "blacklight.toml").is_file()

    lines = install_log.read_text().splitlines()
    assert "install_common" in lines
    assert "install_fonts_unix" in lines
    assert "pull_palettes" in lines


def test_install_sh_installs_missing_deps_brew(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo_brew"
    repo.mkdir()
    shutil.copy(repo_root / "install.sh", repo / "install.sh")
    shutil.copytree(repo_root / "scripts", repo / "scripts")
    install_log = tmp_path / "install_brew.log"
    create_stub_install(repo / "scripts" / "install.sh", install_log)
    create_stub_install_common(repo / "scripts" / "install_common.sh", install_log)
    shutil.copytree(repo_root / ".githooks", repo / ".githooks")
    shutil.copytree(repo_root / "palettes", repo / "palettes")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    brew_log = tmp_path / "brew.log"
    (bin_dir / "bash").symlink_to("/bin/bash")
    (bin_dir / "dirname").symlink_to("/usr/bin/dirname")
    create_exe(
        bin_dir / "brew",
        f"#!/usr/bin/env bash\necho \"$@\" >> '{brew_log}'\nif [[ $1 == install ]]; then\n  shift\n  for pkg in \"$@\"; do\n    /bin/touch '{bin_dir}'/$pkg\n    /bin/chmod 755 '{bin_dir}'/$pkg\n  done\nfi\n",
    )
    create_exe(bin_dir / "sudo", "#!/usr/bin/env bash\n\"$@\"\n")

    subprocess.run(["git", "init"], cwd=repo, check=True)

    env = os.environ.copy()
    env.update({
        "OSTYPE": "darwin",
        "PATH": str(bin_dir),
    })

    subprocess.run(["/bin/bash", "install.sh"], cwd=repo, check=True, env=env)

    lines = brew_log.read_text().splitlines()
    assert any("install" in line for line in lines)
    assert any("curl" in line for line in lines)
    assert any("unzip" in line for line in lines)
    assert any("git" in line for line in lines)
    assert "install_common" in install_log.read_text().splitlines()


def test_install_sh_installs_missing_deps_apt(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo_apt"
    repo.mkdir()
    shutil.copy(repo_root / "install.sh", repo / "install.sh")
    shutil.copytree(repo_root / "scripts", repo / "scripts")
    install_log = tmp_path / "install_apt.log"
    create_stub_install(repo / "scripts" / "install.sh", install_log)
    create_stub_install_common(repo / "scripts" / "install_common.sh", install_log)
    shutil.copytree(repo_root / ".githooks", repo / ".githooks")
    shutil.copytree(repo_root / "palettes", repo / "palettes")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    apt_log = tmp_path / "apt.log"
    (bin_dir / "bash").symlink_to("/bin/bash")
    (bin_dir / "dirname").symlink_to("/usr/bin/dirname")
    create_exe(
        bin_dir / "apt-get",
        f"#!/usr/bin/env bash\necho \"$@\" >> '{apt_log}'\nif [[ $1 == install ]]; then\n  shift\n  for pkg in \"$@\"; do\n    /bin/touch '{bin_dir}'/$pkg\n    /bin/chmod 755 '{bin_dir}'/$pkg\n  done\nfi\n",
    )
    create_exe(bin_dir / "sudo", "#!/usr/bin/env bash\n\"$@\"\n")

    subprocess.run(["git", "init"], cwd=repo, check=True)

    env = os.environ.copy()
    env.update({
        "OSTYPE": "linux-gnu",
        "PATH": str(bin_dir),
    })

    subprocess.run(["/bin/bash", "install.sh"], cwd=repo, check=True, env=env)

    lines = apt_log.read_text().splitlines()
    assert any("install" in line for line in lines)
    assert any("curl" in line for line in lines)
    assert any("unzip" in line for line in lines)
    assert any("git" in line for line in lines)
    assert "install_common" in install_log.read_text().splitlines()
