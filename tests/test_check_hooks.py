import shutil
import subprocess
from pathlib import Path
import pytest

@pytest.mark.skipif(shutil.which("bash") is None, reason="requires bash")
def test_check_hooks_reports_path(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    shutil.copytree(repo_root / "scripts", repo / "scripts")
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=repo, check=True)
    result = subprocess.run(["bash", "scripts/check-hooks.sh"], cwd=repo, capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout.strip() == "Git hooks path is set to '.githooks'"
    assert result.stderr == ""

@pytest.mark.skipif(shutil.which("bash") is None, reason="requires bash")
def test_check_hooks_reports_error_when_unset(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    shutil.copytree(repo_root / "scripts", repo / "scripts")
    subprocess.run(["git", "init"], cwd=repo, check=True)
    result = subprocess.run(["bash", "scripts/check-hooks.sh"], cwd=repo, capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout == ""
    assert "Git hooks are not configured" in result.stderr
