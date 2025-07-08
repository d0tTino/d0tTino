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
    install_log = tmp_path / "install.log"
    create_exe(
        repo / "scripts" / "install.sh",
        f"#!/usr/bin/env bash\n" f"echo install >> '{install_log}'\n",
    )
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
    assert install_log.read_text().strip() == "install"


def test_install_sh_runs_without_ostype(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo_no_ostype"
    repo.mkdir()
    shutil.copy(repo_root / "install.sh", repo / "install.sh")
    shutil.copytree(repo_root / "scripts", repo / "scripts")
    install_log = tmp_path / "install_no_ostype.log"
    create_exe(
        repo / "scripts" / "install.sh",
        f"#!/usr/bin/env bash\n" f"echo install >> '{install_log}'\n",
    )
    shutil.copytree(repo_root / ".githooks", repo / ".githooks")
    shutil.copytree(repo_root / "palettes", repo / "palettes")

    subprocess.run(["git", "init"], cwd=repo, check=True)
    env = os.environ.copy()
    env.pop("OSTYPE", None)
    subprocess.run(["/bin/bash", "install.sh"], cwd=repo, check=True, env=env)

    assert (repo / "palettes" / "blacklight.toml").is_file()
    assert install_log.read_text().strip() == "install"


def test_install_sh_installs_nerd_font_macos(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo_macos"
    repo.mkdir()
    shutil.copy(repo_root / "install.sh", repo / "install.sh")
    shutil.copytree(repo_root / "scripts", repo / "scripts")
    install_log = tmp_path / "install_macos.log"
    create_exe(
        repo / "scripts" / "install.sh",
        f"#!/usr/bin/env bash\n" f"echo install >> '{install_log}'\n",
    )
    shutil.copytree(repo_root / ".githooks", repo / ".githooks")
    shutil.copytree(repo_root / "palettes", repo / "palettes")

    subprocess.run(["git", "init"], cwd=repo, check=True)

    env = os.environ.copy()
    env["OSTYPE"] = "darwin"
    subprocess.run(["/bin/bash", "install.sh"], cwd=repo, check=True, env=env)

    assert install_log.read_text().strip() == "install"
