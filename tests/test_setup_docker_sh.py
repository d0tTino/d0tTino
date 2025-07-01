import os
import subprocess
import shutil
from pathlib import Path


def test_setup_docker_sh_requires_docker(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "Dockerfile").write_text("FROM scratch\n")
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    shutil.copy(Path('scripts/setup-docker.sh'), scripts_dir / 'setup-docker.sh')

    env = {"PATH": str(tmp_path / 'bin')}
    (tmp_path / 'bin').mkdir()

    result = subprocess.run(
        ["/bin/bash", "scripts/setup-docker.sh"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "docker is required" in result.stderr


def test_setup_docker_sh_custom_image(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "Dockerfile").write_text("FROM scratch\n")
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    shutil.copy(Path("scripts/setup-docker.sh"), scripts_dir / "setup-docker.sh")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    cmd_log = tmp_path / "docker_cmd.log"

    def create_exe(path: Path) -> None:
        path.write_text(f"#!/usr/bin/env bash\necho \"$@\" >> '{cmd_log}'\n")
        path.chmod(0o755)

    create_exe(bin_dir / "docker")

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    subprocess.run(
        ["/bin/bash", "scripts/setup-docker.sh", "--image", "custom:latest"],
        cwd=repo,
        env=env,
        check=True,
    )

    lines = cmd_log.read_text().splitlines()
    assert any("build" in line and "custom:latest" in line for line in lines)
    assert any("run" in line and "custom:latest" in line for line in lines)
