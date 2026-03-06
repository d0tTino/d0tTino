import os
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def create_exe(path: Path, contents: str = "#!/usr/bin/env bash\n") -> None:
    path.write_text(contents, encoding="utf-8")
    path.chmod(0o755)


def _copy_setup_wsl(repo: Path) -> None:
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO_ROOT / "scripts" / "setup-wsl.sh", scripts_dir / "setup-wsl.sh")
    (scripts_dir / "setup-wsl.sh").chmod(0o755)


def test_setup_wsl_delegates_to_install_common_with_explicit_flags(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _copy_setup_wsl(repo)

    install_log = tmp_path / "install_common.log"
    create_exe(
        repo / "scripts" / "install_common.sh",
        f"#!/usr/bin/env bash\nprintf '%s\\n' \"$*\" >> '{install_log}'\n",
    )

    env = os.environ.copy()
    env.update({"PATH": "/usr/bin:/bin", "HOME": str(tmp_path / "home")})

    subprocess.run(["/bin/bash", "scripts/setup-wsl.sh"], cwd=repo, check=True, env=env)

    assert install_log.read_text(encoding="utf-8").splitlines() == [
        "--terminal ghostty --set-default-shell=force"
    ]


def test_setup_wsl_passes_host_override_to_install_common(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _copy_setup_wsl(repo)

    install_log = tmp_path / "install_common.log"
    create_exe(
        repo / "scripts" / "install_common.sh",
        f"#!/usr/bin/env bash\nprintf '%s\\n' \"$*\" >> '{install_log}'\n",
    )

    env = os.environ.copy()
    env.update({"PATH": "/usr/bin:/bin", "HOME": str(tmp_path / "home")})

    subprocess.run(
        ["/bin/bash", "scripts/setup-wsl.sh", "--host", "wsl-host"],
        cwd=repo,
        check=True,
        env=env,
    )

    assert install_log.read_text(encoding="utf-8").splitlines() == [
        "--terminal ghostty --set-default-shell=force --host wsl-host"
    ]


def test_setup_wsl_uses_install_common_as_single_dependency_plugin_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _copy_setup_wsl(repo)

    install_log = tmp_path / "install_common.log"
    apt_log = tmp_path / "apt.log"
    git_log = tmp_path / "git.log"

    create_exe(
        repo / "scripts" / "install_common.sh",
        f"#!/usr/bin/env bash\nprintf '%s\\n' \"$*\" >> '{install_log}'\n",
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    create_exe(bin_dir / "apt-get", f"#!/usr/bin/env bash\necho \"$@\" >> '{apt_log}'\n")
    create_exe(bin_dir / "git", f"#!/usr/bin/env bash\necho \"$@\" >> '{git_log}'\n")

    env = os.environ.copy()
    env.update({"PATH": f"{tmp_path / 'bin'}:/usr/bin:/bin", "HOME": str(tmp_path / "home")})

    subprocess.run(["/bin/bash", "scripts/setup-wsl.sh"], cwd=repo, check=True, env=env)

    assert install_log.exists()
    assert not apt_log.exists()
    assert not git_log.exists()
