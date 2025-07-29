import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("bash") is None, reason="requires bash")
def test_check_changed_code_md_only(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy(repo_root / "scripts" / "check-changed-code.sh", repo / "check-changed-code.sh")
    subprocess.run(["git", "init"], cwd=repo, check=True)
    (repo / "README.md").write_text("initial\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)
    base_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()

    (repo / "docs.md").write_text("docs change\n", encoding="utf-8")
    subprocess.run(["git", "add", "docs.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "docs"], cwd=repo, check=True)
    head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()

    out_file = repo / "output.txt"
    env = os.environ.copy()
    env.update({
        "EVENT_NAME": "push",
        "BEFORE": base_sha,
        "HEAD_SHA": head_sha,
        "GITHUB_OUTPUT": str(out_file),
    })
    subprocess.run(["bash", "check-changed-code.sh"], cwd=repo, env=env, check=True)

    assert out_file.read_text().strip() == "code_changed=false"


@pytest.mark.skipif(shutil.which("bash") is None, reason="requires bash")
def test_check_changed_code_python_change(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy(repo_root / "scripts" / "check-changed-code.sh", repo / "check-changed-code.sh")
    subprocess.run(["git", "init"], cwd=repo, check=True)
    (repo / "README.md").write_text("initial\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)
    base_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()

    (repo / "main.py").write_text("print('hello')\n", encoding="utf-8")
    subprocess.run(["git", "add", "main.py"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "feat: add python"], cwd=repo, check=True)
    head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()

    out_file = repo / "output.txt"
    env = os.environ.copy()
    env.update({
        "EVENT_NAME": "push",
        "BEFORE": base_sha,
        "HEAD_SHA": head_sha,
        "GITHUB_OUTPUT": str(out_file),
    })
    subprocess.run(["bash", "check-changed-code.sh"], cwd=repo, env=env, check=True)

    assert out_file.read_text().strip() == "code_changed=true"
