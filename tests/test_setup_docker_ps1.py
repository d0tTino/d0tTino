import os
import shutil
import subprocess
from pathlib import Path

import pytest


def create_exe(path: Path, contents: str = "#!/usr/bin/env bash\n") -> None:
    path.write_text(contents)
    path.chmod(0o755)


@pytest.mark.skipif(
    shutil.which("pwsh") is None and shutil.which("powershell") is None,
    reason="requires PowerShell",
)
def test_setup_docker_ps1_invokes_docker(tmp_path: Path) -> None:
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copytree(Path(__file__).resolve().parents[1] / "scripts", repo / "scripts")
    (repo / "Dockerfile").write_text("FROM scratch\n")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    cmd_log = tmp_path / "docker_cmd.log"
    create_exe(
        bin_dir / "docker",
        f"#!/usr/bin/env bash\necho \"$@\" >> '{cmd_log}'\n",
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    subprocess.run(
        [pwsh, "-NoLogo", "-NoProfile", "-File", str(repo / "scripts/setup-docker.ps1"), "-ImageName", "custom:latest"],
        cwd=repo,
        env=env,
        check=True,
    )

    lines = cmd_log.read_text().splitlines()
    assert any("build" in line and "custom:latest" in line for line in lines)
    assert any("run" in line and "custom:latest" in line for line in lines)
