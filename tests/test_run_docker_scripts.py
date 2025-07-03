import os
import shutil
import subprocess
from pathlib import Path

import pytest


def create_exe(path: Path, contents: str = "#!/usr/bin/env bash\n") -> None:
    path.write_text(contents)
    path.chmod(0o755)


@pytest.mark.parametrize(
    "script_name,args,expected",
    [
        ("run-neko.sh", ["--help"], "compose up neko --help"),
        ("run-romm.sh", ["--help"], "compose up romm --help"),
        ("run-nextcloud.sh", ["--help"], "compose up nextcloud --help"),
        ("run-mattermost.sh", ["--help"], "compose up mattermost --help"),
        ("run-service.sh", ["romm", "--help"], "compose up romm --help"),
    ],
)
def test_run_script_help_invokes_docker(
    tmp_path: Path, script_name: str, args: list[str], expected: str
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    shutil.copy(Path("scripts") / script_name, scripts_dir / script_name)
    shutil.copy(Path("scripts") / "run-service.sh", scripts_dir / "run-service.sh")

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
        ["/bin/bash", f"scripts/{script_name}", *args],
        cwd=repo,
        env=env,
        check=True,
    )

    assert cmd_log.read_text().strip() == expected


@pytest.mark.parametrize(
    "script_name,args",
    [
        ("run-neko.sh", []),
        ("run-romm.sh", []),
        ("run-nextcloud.sh", []),
        ("run-mattermost.sh", []),
        ("run-service.sh", ["romm"]),
    ],
)
def test_run_script_requires_docker(tmp_path: Path, script_name: str, args: list[str]) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    shutil.copy(Path("scripts") / script_name, scripts_dir / script_name)
    shutil.copy(Path("scripts") / "run-service.sh", scripts_dir / "run-service.sh")

    env = {"PATH": str(tmp_path / "bin")}
    (tmp_path / "bin").mkdir()

    result = subprocess.run(
        ["/bin/bash", f"scripts/{script_name}", *args],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "docker is required" in result.stderr
