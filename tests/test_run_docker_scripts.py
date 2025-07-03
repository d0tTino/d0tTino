import os
import shutil
import subprocess
from pathlib import Path

import pytest


def create_exe(path: Path, contents: str = "#!/usr/bin/env bash\n") -> None:
    path.write_text(contents)
    path.chmod(0o755)


@pytest.mark.parametrize("script_name,service", [
    ("run-neko.sh", "neko"),
    ("run-romm.sh", "romm"),
    ("run-nextcloud.sh", "nextcloud"),
])
def test_run_script_help_invokes_docker(tmp_path: Path, script_name: str, service: str) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    shutil.copy(Path("scripts") / script_name, scripts_dir / script_name)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    cmd_log = tmp_path / "docker_cmd.log"
    create_exe(
        bin_dir / "docker",
        f"#!/usr/bin/env bash\necho \"$@\" >> '{cmd_log}'\n",
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    subprocess.run([
        "/bin/bash",
        f"scripts/{script_name}",
        "--help",
    ], cwd=repo, env=env, check=True)

    assert cmd_log.read_text().strip() == f"compose up {service} --help"


@pytest.mark.parametrize("script_name", ["run-neko.sh", "run-romm.sh", "run-nextcloud.sh"])
def test_run_script_requires_docker(tmp_path: Path, script_name: str) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    shutil.copy(Path("scripts") / script_name, scripts_dir / script_name)

    env = {"PATH": str(tmp_path / "bin")}
    (tmp_path / "bin").mkdir()

    result = subprocess.run(
        ["/bin/bash", f"scripts/{script_name}"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "docker is required" in result.stderr
