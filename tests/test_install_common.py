import os
import shutil
import subprocess
from pathlib import Path

from tests.stubs import create_stub_pwsh


def create_exe(path: Path, contents: str = "#!/usr/bin/env bash\n") -> None:
    path.write_text(contents, encoding="utf-8")
    path.chmod(0o755)


def test_install_common_runs_without_ostype(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    repo.mkdir()

    scripts_dir = repo / "scripts"
    helpers_dir = scripts_dir / "helpers"
    helpers_dir.mkdir(parents=True)

    shutil.copy(repo_root / "scripts" / "install_common.sh", scripts_dir / "install_common.sh")

    log = tmp_path / "install.log"
    (scripts_dir / "setup-hooks.sh").write_text(
        f"#!/usr/bin/env bash\necho setup_hooks >> '{log}'\n", encoding="utf-8"
    )
    (helpers_dir / "install_fonts.sh").write_text(
        f"#!/usr/bin/env bash\necho install_fonts >> '{log}'\n", encoding="utf-8"
    )
    (helpers_dir / "sync_palettes.sh").write_text(
        f"#!/usr/bin/env bash\necho sync_palettes >> '{log}'\n", encoding="utf-8"
    )

    for f in [scripts_dir / "setup-hooks.sh", helpers_dir / "install_fonts.sh", helpers_dir / "sync_palettes.sh"]:
        f.chmod(0o755)

    env = os.environ.copy()
    env.pop("OSTYPE", None)

    subprocess.run(["/bin/bash", "scripts/install_common.sh"], cwd=repo, check=True, env=env)

    lines = log.read_text().splitlines()
    assert "setup_hooks" in lines
    assert "install_fonts" in lines
    assert "sync_palettes" in lines


def test_install_common_installs_missing_deps_dnf(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo_dnf"
    repo.mkdir()

    scripts_dir = repo / "scripts"
    helpers_dir = scripts_dir / "helpers"
    helpers_dir.mkdir(parents=True)

    shutil.copy(repo_root / "scripts" / "install_common.sh", scripts_dir / "install_common.sh")

    log = tmp_path / "install.log"
    (scripts_dir / "setup-hooks.sh").write_text(
        f"#!/usr/bin/env bash\necho setup_hooks >> '{log}'\n", encoding="utf-8"
    )
    (helpers_dir / "install_fonts.sh").write_text(
        f"#!/usr/bin/env bash\necho install_fonts >> '{log}'\n", encoding="utf-8"
    )
    (helpers_dir / "sync_palettes.sh").write_text(
        f"#!/usr/bin/env bash\necho sync_palettes >> '{log}'\n", encoding="utf-8"
    )
    for f in [scripts_dir / "setup-hooks.sh", helpers_dir / "install_fonts.sh", helpers_dir / "sync_palettes.sh"]:
        f.chmod(0o755)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    dnf_log = tmp_path / "dnf.log"
    create_exe(
        bin_dir / "dnf",
        f"#!/usr/bin/env bash\necho \"$@\" >> '{dnf_log}'\nif [[ $1 == install ]]; then\n  shift\n  for pkg in \"$@\"; do\n    /bin/touch '{bin_dir}'/$pkg\n    /bin/chmod 755 '{bin_dir}'/$pkg\n  done\nfi\n",
    )
    create_exe(bin_dir / "sudo", "#!/usr/bin/env bash\n\"$@\"\n")
    (bin_dir / "bash").symlink_to("/bin/bash")
    (bin_dir / "dirname").symlink_to("/usr/bin/dirname")

    subprocess.run(["git", "init"], cwd=repo, check=True)

    env = os.environ.copy()
    env.update({
        "OSTYPE": "linux-gnu",
        "PATH": str(bin_dir),
    })

    subprocess.run(["/bin/bash", "scripts/install_common.sh"], cwd=repo, check=True, env=env)

    lines = dnf_log.read_text().splitlines()
    assert any("install" in line for line in lines)
    assert any("curl" in line for line in lines)
    assert any("unzip" in line for line in lines)
    assert any("git" in line for line in lines)


def test_install_common_installs_missing_deps_pacman(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo_pacman"
    repo.mkdir()

    scripts_dir = repo / "scripts"
    helpers_dir = scripts_dir / "helpers"
    helpers_dir.mkdir(parents=True)

    shutil.copy(repo_root / "scripts" / "install_common.sh", scripts_dir / "install_common.sh")

    log = tmp_path / "install.log"
    (scripts_dir / "setup-hooks.sh").write_text(
        f"#!/usr/bin/env bash\necho setup_hooks >> '{log}'\n", encoding="utf-8"
    )
    (helpers_dir / "install_fonts.sh").write_text(
        f"#!/usr/bin/env bash\necho install_fonts >> '{log}'\n", encoding="utf-8"
    )
    (helpers_dir / "sync_palettes.sh").write_text(
        f"#!/usr/bin/env bash\necho sync_palettes >> '{log}'\n", encoding="utf-8"
    )
    for f in [scripts_dir / "setup-hooks.sh", helpers_dir / "install_fonts.sh", helpers_dir / "sync_palettes.sh"]:
        f.chmod(0o755)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    pac_log = tmp_path / "pacman.log"
    create_exe(
        bin_dir / "pacman",
        f"#!/usr/bin/env bash\necho \"$@\" >> '{pac_log}'\nif [[ $1 == -S ]]; then\n  shift\n  if [[ $1 == --noconfirm ]]; then\n    shift\n  fi\n  for pkg in \"$@\"; do\n    /bin/touch '{bin_dir}'/$pkg\n    /bin/chmod 755 '{bin_dir}'/$pkg\n  done\nfi\n",
    )
    create_exe(bin_dir / "sudo", "#!/usr/bin/env bash\n\"$@\"\n")
    (bin_dir / "bash").symlink_to("/bin/bash")
    (bin_dir / "dirname").symlink_to("/usr/bin/dirname")

    subprocess.run(["git", "init"], cwd=repo, check=True)

    env = os.environ.copy()
    env.update({
        "OSTYPE": "linux-gnu",
        "PATH": str(bin_dir),
    })

    subprocess.run(["/bin/bash", "scripts/install_common.sh"], cwd=repo, check=True, env=env)

    lines = pac_log.read_text().splitlines()
    assert any("-S" in line for line in lines)
    assert any("curl" in line for line in lines)
    assert any("unzip" in line for line in lines)
    assert any("git" in line for line in lines)


def test_install_common_setup_flags_linux(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo_setup_linux"
    repo.mkdir()

    scripts_dir = repo / "scripts"
    helpers_dir = scripts_dir / "helpers"
    helpers_dir.mkdir(parents=True)

    shutil.copy(repo_root / "scripts" / "install_common.sh", scripts_dir / "install_common.sh")

    log = tmp_path / "install.log"
    (scripts_dir / "setup-hooks.sh").write_text(
        f"#!/usr/bin/env bash\necho setup_hooks >> '{log}'\n", encoding="utf-8"
    )
    (helpers_dir / "install_fonts.sh").write_text(
        f"#!/usr/bin/env bash\necho install_fonts >> '{log}'\n", encoding="utf-8"
    )
    (helpers_dir / "sync_palettes.sh").write_text(
        f"#!/usr/bin/env bash\necho sync_palettes >> '{log}'\n", encoding="utf-8"
    )
    (scripts_dir / "setup-wsl.sh").write_text(
        f"#!/usr/bin/env bash\necho setup_wsl >> '{log}'\n", encoding="utf-8"
    )
    (scripts_dir / "setup-docker.sh").write_text(
        f"#!/usr/bin/env bash\necho setup_docker \"$@\" >> '{log}'\n", encoding="utf-8"
    )

    for f in [
        scripts_dir / "setup-hooks.sh",
        helpers_dir / "install_fonts.sh",
        helpers_dir / "sync_palettes.sh",
        scripts_dir / "setup-wsl.sh",
        scripts_dir / "setup-docker.sh",
    ]:
        f.chmod(0o755)

    env = os.environ.copy()
    env["OSTYPE"] = "linux-gnu"
    subprocess.run(
        [
            "/bin/bash",
            "scripts/install_common.sh",
            "--setup-wsl",
            "--setup-docker",
            "--image",
            "custom:latest",
        ],
        cwd=repo,
        check=True,
        env=env,
    )

    lines = log.read_text().splitlines()
    assert "setup_hooks" in lines
    assert "install_fonts" in lines
    assert "sync_palettes" in lines
    assert "setup_wsl" in lines
    assert any("setup_docker" in line for line in lines)
    assert any("custom:latest" in line for line in lines)


def test_install_common_setup_flags_windows(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo_setup_windows"
    repo.mkdir()

    scripts_dir = repo / "scripts"
    helpers_dir = scripts_dir / "helpers"
    helpers_dir.mkdir(parents=True)

    shutil.copy(repo_root / "scripts" / "install_common.sh", scripts_dir / "install_common.sh")

    log = tmp_path / "install.log"
    (helpers_dir / "install_common.ps1").write_text(
        f"#!/usr/bin/env bash\necho install_common_ps1 >> '{log}'\n",
        encoding="utf-8",
    )

    for f in [helpers_dir / "install_common.ps1"]:
        f.chmod(0o755)

    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    create_stub_pwsh(stub_dir / "pwsh", log)

    env = os.environ.copy()
    env.update({
        "OSTYPE": "msys",
        "PATH": f"{stub_dir}:{env['PATH']}",
        "STUB_IS_WINDOWS": "1",
    })

    subprocess.run(
        [
            "/bin/bash",
            "scripts/install_common.sh",
            "--setup-wsl",
            "--setup-docker",
            "--image",
            "custom:latest",
        ],
        cwd=repo,
        check=True,
        env=env,
    )

    lines = log.read_text().splitlines()
    assert "fix-path.ps1" in lines
    assert "install_common.ps1" in lines
    assert "setup-wsl.ps1" in lines
    assert "setup-docker.ps1" in lines
