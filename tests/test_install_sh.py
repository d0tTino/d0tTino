import shutil
import subprocess
from pathlib import Path


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
