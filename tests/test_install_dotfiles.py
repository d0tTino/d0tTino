import os
import shutil
import subprocess
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("stow") is None, reason="requires bash and stow")
def test_install_dotfiles(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    result = subprocess.run([
        "/bin/bash",
        str(REPO_ROOT / "scripts" / "install_dotfiles.sh"),
        "--target",
        str(tmp_path),
    ], capture_output=True, text=True, env=env, cwd=REPO_ROOT, check=True)
    assert "LINK: config.toml" in result.stderr

    link = tmp_path / "config.toml"
    assert link.is_symlink()
    assert link.resolve().samefile(REPO_ROOT / "dotfiles" / "btm" / "config.toml")

    mtime = link.lstat().st_mtime
    dry = subprocess.run([
        "/bin/bash",
        str(REPO_ROOT / "scripts" / "install_dotfiles.sh"),
        "--dry-run",
        "--target",
        str(tmp_path),
    ], capture_output=True, text=True, env=env, cwd=REPO_ROOT, check=True)

    assert "simulation mode" in dry.stderr
    assert link.lstat().st_mtime == mtime
