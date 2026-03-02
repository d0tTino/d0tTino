import os
import shutil
import subprocess
from pathlib import Path

from tests.stubs import create_stub_pwsh


def create_exe(path: Path, contents: str = "#!/usr/bin/env bash\n") -> None:
    path.write_text(contents, encoding="utf-8")
    path.chmod(0o755)


def create_git_stub(path: Path, log_path: Path) -> None:
    create_exe(
        path,
        f"#!/usr/bin/env bash\necho \"$@\" >> '{log_path}'\nif [[ $1 == clone ]]; then\n  /bin/mkdir -p \"$3/.git\"\nfi\n",
    )


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
    (scripts_dir / "setup-nvim.sh").write_text(
        f"#!/usr/bin/env bash\necho setup_nvim >> '{log}'\n", encoding="utf-8"
    )
    (helpers_dir / "install_fonts.sh").write_text(
        f"#!/usr/bin/env bash\necho install_fonts >> '{log}'\n", encoding="utf-8"
    )
    (helpers_dir / "sync_palettes.sh").write_text(
        f"#!/usr/bin/env bash\necho sync_palettes >> '{log}'\n", encoding="utf-8"
    )

    for f in [
        scripts_dir / "setup-hooks.sh",
        scripts_dir / "setup-nvim.sh",
        helpers_dir / "install_fonts.sh",
        helpers_dir / "sync_palettes.sh",
    ]:
        f.chmod(0o755)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    git_log = tmp_path / "git.log"
    create_exe(bin_dir / "curl")
    create_exe(bin_dir / "unzip")
    create_exe(bin_dir / "zsh")
    create_exe(bin_dir / "starship", "#!/usr/bin/env bash\nif [[ $1 == init && $2 == zsh ]]; then\n  echo 'STARSHIP_INIT'\nfi\n")
    create_git_stub(bin_dir / "git", git_log)
    (bin_dir / "bash").symlink_to("/bin/bash")
    (bin_dir / "dirname").symlink_to("/usr/bin/dirname")

    env = os.environ.copy()
    env.pop("OSTYPE", None)
    env.update({"PATH": f"{bin_dir}:/usr/bin:/bin"})

    subprocess.run(["/bin/bash", "scripts/install_common.sh"], cwd=repo, check=True, env=env)

    lines = log.read_text().splitlines()
    assert "setup_hooks" in lines
    assert "setup_nvim" in lines
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
    git_log = tmp_path / "git.log"
    create_exe(
        bin_dir / "dnf",
        f"#!/usr/bin/env bash\necho \"$@\" >> '{dnf_log}'\nif [[ $1 == install ]]; then\n  shift\n  if [[ $1 == -y ]]; then\n    shift\n  fi\n  for pkg in \"$@\"; do\n    if [[ $pkg == git ]]; then\n      cat > '{bin_dir}'/git <<'EOF'\n#!/usr/bin/env bash\necho \"$@\" >> '{git_log}'\nif [[ $1 == clone ]]; then\n  /bin/mkdir -p \"$3/.git\"\nfi\nEOF\n      /bin/chmod 755 '{bin_dir}'/git\n    elif [[ $pkg == starship ]]; then\n      cat > '{bin_dir}'/starship <<'EOF'\n#!/usr/bin/env bash\nif [[ $1 == init && $2 == zsh ]]; then\n  echo 'STARSHIP_INIT'\nfi\nEOF\n      /bin/chmod 755 '{bin_dir}'/starship\n    else\n      cat > '{bin_dir}'/$pkg <<'EOF'\n#!/usr/bin/env bash\nexit 0\nEOF\n      /bin/chmod 755 '{bin_dir}'/$pkg\n    fi\n  done\nfi\n",
    )
    create_exe(bin_dir / "sudo", "#!/usr/bin/env bash\n\"$@\"\n")
    (bin_dir / "bash").symlink_to("/bin/bash")
    (bin_dir / "dirname").symlink_to("/usr/bin/dirname")
    (bin_dir / "cat").symlink_to("/bin/cat")

    subprocess.run(["git", "init"], cwd=repo, check=True)

    env = os.environ.copy()
    env.update({"OSTYPE": "linux-gnu", "PATH": str(bin_dir)})

    subprocess.run(["/bin/bash", "scripts/install_common.sh"], cwd=repo, check=True, env=env)

    lines = dnf_log.read_text().splitlines()
    assert any("install" in line for line in lines)
    assert any("curl" in line for line in lines)
    assert any("unzip" in line for line in lines)
    assert any("git" in line for line in lines)
    assert any("zsh" in line for line in lines)
    assert any("starship" in line for line in lines)


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
    git_log = tmp_path / "git.log"
    create_exe(
        bin_dir / "pacman",
        f"#!/usr/bin/env bash\necho \"$@\" >> '{pac_log}'\nif [[ $1 == -S ]]; then\n  shift\n  if [[ $1 == --noconfirm ]]; then\n    shift\n  fi\n  for pkg in \"$@\"; do\n    if [[ $pkg == git ]]; then\n      cat > '{bin_dir}'/git <<'EOF'\n#!/usr/bin/env bash\necho \"$@\" >> '{git_log}'\nif [[ $1 == clone ]]; then\n  /bin/mkdir -p \"$3/.git\"\nfi\nEOF\n      /bin/chmod 755 '{bin_dir}'/git\n    elif [[ $pkg == starship ]]; then\n      cat > '{bin_dir}'/starship <<'EOF'\n#!/usr/bin/env bash\nif [[ $1 == init && $2 == zsh ]]; then\n  echo 'STARSHIP_INIT'\nfi\nEOF\n      /bin/chmod 755 '{bin_dir}'/starship\n    else\n      cat > '{bin_dir}'/$pkg <<'EOF'\n#!/usr/bin/env bash\nexit 0\nEOF\n      /bin/chmod 755 '{bin_dir}'/$pkg\n    fi\n  done\nfi\n",
    )
    create_exe(bin_dir / "sudo", "#!/usr/bin/env bash\n\"$@\"\n")
    (bin_dir / "bash").symlink_to("/bin/bash")
    (bin_dir / "dirname").symlink_to("/usr/bin/dirname")
    (bin_dir / "cat").symlink_to("/bin/cat")

    subprocess.run(["git", "init"], cwd=repo, check=True)

    env = os.environ.copy()
    env.update({"OSTYPE": "linux-gnu", "PATH": str(bin_dir)})

    subprocess.run(["/bin/bash", "scripts/install_common.sh"], cwd=repo, check=True, env=env)

    lines = pac_log.read_text().splitlines()
    assert any("-S" in line for line in lines)
    assert any("curl" in line for line in lines)
    assert any("unzip" in line for line in lines)
    assert any("git" in line for line in lines)
    assert any("zsh" in line for line in lines)
    assert any("starship" in line for line in lines)


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

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    git_log = tmp_path / "git.log"
    create_exe(bin_dir / "curl")
    create_exe(bin_dir / "unzip")
    create_exe(bin_dir / "zsh")
    create_exe(bin_dir / "starship", "#!/usr/bin/env bash\nif [[ $1 == init && $2 == zsh ]]; then\n  echo 'STARSHIP_INIT'\nfi\n")
    create_git_stub(bin_dir / "git", git_log)
    (bin_dir / "bash").symlink_to("/bin/bash")
    (bin_dir / "dirname").symlink_to("/usr/bin/dirname")

    env = os.environ.copy()
    env["OSTYPE"] = "linux-gnu"
    env["PATH"] = f"{bin_dir}:/usr/bin:/bin"
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


def test_install_common_installs_zsh_plugins_without_touching_zshrc(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo_zsh"
    repo.mkdir()

    scripts_dir = repo / "scripts"
    helpers_dir = scripts_dir / "helpers"
    helpers_dir.mkdir(parents=True)

    shutil.copy(repo_root / "scripts" / "install_common.sh", scripts_dir / "install_common.sh")

    log = tmp_path / "install.log"
    for path, line in [
        (scripts_dir / "setup-hooks.sh", "setup_hooks"),
        (helpers_dir / "install_fonts.sh", "install_fonts"),
        (helpers_dir / "sync_palettes.sh", "sync_palettes"),
    ]:
        path.write_text(f"#!/usr/bin/env bash\necho {line} >> '{log}'\n", encoding="utf-8")
        path.chmod(0o755)

    home_dir = tmp_path / "home"
    home_dir.mkdir()
    zshrc = home_dir / ".zshrc"
    existing_zshrc = "# existing\n"
    zshrc.write_text(existing_zshrc, encoding="utf-8")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    apt_log = tmp_path / "apt.log"
    git_log = tmp_path / "git.log"

    create_exe(
        bin_dir / "apt-get",
        f"#!/usr/bin/env bash\necho \"$@\" >> '{apt_log}'\nif [[ $1 == install ]]; then\n  shift\n  if [[ $1 == -y ]]; then\n    shift\n  fi\n  for pkg in \"$@\"; do\n    /bin/touch '{bin_dir}'/$pkg\n    /bin/chmod 755 '{bin_dir}'/$pkg\n  done\nfi\n",
    )
    create_exe(
        bin_dir / "git",
        f"#!/usr/bin/env bash\necho \"$@\" >> '{git_log}'\nif [[ $1 == clone ]]; then\n  /bin/mkdir -p \"$3/.git\"\nfi\n",
    )
    create_exe(bin_dir / "starship", "#!/usr/bin/env bash\nif [[ $1 == init && $2 == zsh ]]; then\n  echo 'STARSHIP_INIT'\nfi\n")
    create_exe(bin_dir / "sudo", "#!/usr/bin/env bash\n\"$@\"\n")
    (bin_dir / "bash").symlink_to("/bin/bash")
    (bin_dir / "dirname").symlink_to("/usr/bin/dirname")

    env = os.environ.copy()
    env.update({
        "OSTYPE": "linux-gnu",
        "PATH": f"{bin_dir}:/usr/bin:/bin",
        "HOME": str(home_dir),
        "SHELL": "/bin/bash",
    })

    subprocess.run(["/bin/bash", "scripts/install_common.sh"], cwd=repo, check=True, env=env)

    zshrc_content = zshrc.read_text(encoding="utf-8")
    assert zshrc_content == existing_zshrc

    apt_lines = apt_log.read_text(encoding="utf-8").splitlines()
    assert any("install -y" in line and "zsh" in line for line in apt_lines)

    git_lines = git_log.read_text(encoding="utf-8").splitlines()
    assert sum(1 for line in git_lines if line.startswith("clone ")) == 2


def test_install_common_does_not_append_plugin_marker_block_to_existing_zshrc(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo_zsh_idempotent"
    repo.mkdir()

    scripts_dir = repo / "scripts"
    helpers_dir = scripts_dir / "helpers"
    helpers_dir.mkdir(parents=True)

    shutil.copy(repo_root / "scripts" / "install_common.sh", scripts_dir / "install_common.sh")

    for path in [scripts_dir / "setup-hooks.sh", helpers_dir / "install_fonts.sh", helpers_dir / "sync_palettes.sh"]:
        path.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        path.chmod(0o755)

    home_dir = tmp_path / "home"
    home_dir.mkdir()

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    git_log = tmp_path / "git.log"

    create_exe(bin_dir / "curl")
    create_exe(bin_dir / "unzip")
    create_exe(bin_dir / "zsh")
    create_exe(bin_dir / "starship", "#!/usr/bin/env bash\nif [[ $1 == init && $2 == zsh ]]; then\n  echo 'STARSHIP_INIT'\nfi\n")
    create_exe(
        bin_dir / "git",
        f"#!/usr/bin/env bash\necho \"$@\" >> '{git_log}'\nif [[ $1 == clone ]]; then\n  /bin/mkdir -p \"$3/.git\"\nfi\n",
    )
    create_exe(bin_dir / "sudo", "#!/usr/bin/env bash\n\"$@\"\n")
    (bin_dir / "bash").symlink_to("/bin/bash")
    (bin_dir / "dirname").symlink_to("/usr/bin/dirname")

    env = os.environ.copy()
    env.update({
        "OSTYPE": "linux-gnu",
        "PATH": f"{bin_dir}:/usr/bin:/bin",
        "HOME": str(home_dir),
        "SHELL": "/bin/bash",
    })

    zshrc = home_dir / ".zshrc"
    zshrc.write_text("# my custom config\n", encoding="utf-8")

    subprocess.run(["/bin/bash", "scripts/install_common.sh"], cwd=repo, check=True, env=env)

    zshrc_content = zshrc.read_text(encoding="utf-8")
    assert zshrc_content == "# my custom config\n"
    assert "# >>> d0tTino zsh plugins >>>" not in zshrc_content
    assert 'eval "$(starship init zsh)"' not in zshrc_content

    clone_lines = [line for line in git_log.read_text(encoding="utf-8").splitlines() if line.startswith("clone ")]
    assert len(clone_lines) == 2




def test_install_common_installs_tpm_during_provisioning(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo_tmux_tpm"
    repo.mkdir()

    scripts_dir = repo / "scripts"
    helpers_dir = scripts_dir / "helpers"
    helpers_dir.mkdir(parents=True)

    shutil.copy(repo_root / "scripts" / "install_common.sh", scripts_dir / "install_common.sh")

    for path in [scripts_dir / "setup-hooks.sh", helpers_dir / "install_fonts.sh", helpers_dir / "sync_palettes.sh"]:
        path.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        path.chmod(0o755)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    git_log = tmp_path / "git.log"

    for exe in ["curl", "unzip", "zsh", "tmux", "nvim", "cargo", "stow", "rg", "fd"]:
        create_exe(bin_dir / exe)
    create_exe(bin_dir / "starship", "#!/usr/bin/env bash\nif [[ $1 == init && $2 == zsh ]]; then\n  echo 'STARSHIP_INIT'\nfi\n")
    create_git_stub(bin_dir / "git", git_log)
    (bin_dir / "bash").symlink_to("/bin/bash")
    (bin_dir / "dirname").symlink_to("/usr/bin/dirname")

    home_dir = tmp_path / "home"
    home_dir.mkdir()

    env = os.environ.copy()
    env.update({"OSTYPE": "linux-gnu", "PATH": f"{bin_dir}:/usr/bin:/bin", "HOME": str(home_dir), "SHELL": "/bin/bash"})

    subprocess.run(["/bin/bash", "scripts/install_common.sh"], cwd=repo, check=True, env=env)

    clone_lines = [line for line in git_log.read_text(encoding="utf-8").splitlines() if line.startswith("clone ")]
    assert any("tmux-plugins/tpm" in line and str(home_dir / ".tmux/plugins/tpm") in line for line in clone_lines)


def test_install_common_skips_tpm_clone_when_repo_exists(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo_tmux_tpm_idempotent"
    repo.mkdir()

    scripts_dir = repo / "scripts"
    helpers_dir = scripts_dir / "helpers"
    helpers_dir.mkdir(parents=True)

    shutil.copy(repo_root / "scripts" / "install_common.sh", scripts_dir / "install_common.sh")

    for path in [scripts_dir / "setup-hooks.sh", helpers_dir / "install_fonts.sh", helpers_dir / "sync_palettes.sh"]:
        path.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        path.chmod(0o755)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    git_log = tmp_path / "git.log"

    for exe in ["curl", "unzip", "zsh", "tmux", "nvim", "cargo", "stow", "rg", "fd"]:
        create_exe(bin_dir / exe)
    create_exe(bin_dir / "starship", "#!/usr/bin/env bash\nif [[ $1 == init && $2 == zsh ]]; then\n  echo 'STARSHIP_INIT'\nfi\n")
    create_git_stub(bin_dir / "git", git_log)
    (bin_dir / "bash").symlink_to("/bin/bash")
    (bin_dir / "dirname").symlink_to("/usr/bin/dirname")

    home_dir = tmp_path / "home"
    (home_dir / ".tmux/plugins/tpm/.git").mkdir(parents=True)

    env = os.environ.copy()
    env.update({"OSTYPE": "linux-gnu", "PATH": f"{bin_dir}:/usr/bin:/bin", "HOME": str(home_dir), "SHELL": "/bin/bash"})

    subprocess.run(["/bin/bash", "scripts/install_common.sh"], cwd=repo, check=True, env=env)

    clone_lines = [line for line in git_log.read_text(encoding="utf-8").splitlines() if line.startswith("clone ")]
    assert not any("tmux-plugins/tpm" in line for line in clone_lines)

def test_install_common_runs_install_dotfiles_with_detected_host(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo_dotfiles"
    repo.mkdir()

    scripts_dir = repo / "scripts"
    helpers_dir = scripts_dir / "helpers"
    helpers_dir.mkdir(parents=True)

    shutil.copy(repo_root / "scripts" / "install_common.sh", scripts_dir / "install_common.sh")

    log = tmp_path / "install.log"
    for path in [scripts_dir / "setup-hooks.sh", helpers_dir / "install_fonts.sh", helpers_dir / "sync_palettes.sh"]:
        path.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        path.chmod(0o755)

    install_dotfiles_log = tmp_path / "install_dotfiles.log"
    (scripts_dir / "install_dotfiles.sh").write_text(
        f"#!/usr/bin/env bash\nprintf '%s\\n' \"$*\" >> '{install_dotfiles_log}'\n",
        encoding="utf-8",
    )
    (scripts_dir / "install_dotfiles.sh").chmod(0o755)

    detected_host = "desktop"
    (repo / "hosts" / detected_host).mkdir(parents=True)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    create_exe(bin_dir / "curl")
    create_exe(bin_dir / "unzip")
    create_exe(bin_dir / "zsh")
    create_exe(bin_dir / "tmux")
    create_exe(bin_dir / "nvim")
    create_exe(bin_dir / "cargo")
    create_exe(bin_dir / "stow")
    create_exe(bin_dir / "starship", "#!/usr/bin/env bash\nif [[ $1 == init && $2 == zsh ]]; then\n  echo 'STARSHIP_INIT'\nfi\n")
    create_git_stub(bin_dir / "git", log)
    create_exe(bin_dir / "hostname", f"#!/usr/bin/env bash\necho '{detected_host}'\n")
    (bin_dir / "bash").symlink_to("/bin/bash")
    (bin_dir / "dirname").symlink_to("/usr/bin/dirname")

    env = os.environ.copy()
    env.update({"OSTYPE": "linux-gnu", "PATH": f"{bin_dir}:/usr/bin:/bin", "HOME": str(tmp_path / 'home')})

    subprocess.run(["/bin/bash", "scripts/install_common.sh"], cwd=repo, check=True, env=env)

    install_dotfiles_calls = install_dotfiles_log.read_text(encoding="utf-8").splitlines()
    assert install_dotfiles_calls == [f"--host {detected_host}"]


def test_install_common_passes_explicit_host_to_install_dotfiles(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo_dotfiles_host"
    repo.mkdir()

    scripts_dir = repo / "scripts"
    helpers_dir = scripts_dir / "helpers"
    helpers_dir.mkdir(parents=True)

    shutil.copy(repo_root / "scripts" / "install_common.sh", scripts_dir / "install_common.sh")

    for path in [scripts_dir / "setup-hooks.sh", helpers_dir / "install_fonts.sh", helpers_dir / "sync_palettes.sh"]:
        path.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        path.chmod(0o755)

    install_dotfiles_log = tmp_path / "install_dotfiles_explicit.log"
    (scripts_dir / "install_dotfiles.sh").write_text(
        f"#!/usr/bin/env bash\nprintf '%s\\n' \"$*\" >> '{install_dotfiles_log}'\n",
        encoding="utf-8",
    )
    (scripts_dir / "install_dotfiles.sh").chmod(0o755)

    (repo / "hosts" / "work_laptop").mkdir(parents=True)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for exe in ["curl", "unzip", "zsh", "tmux", "nvim", "cargo", "stow"]:
        create_exe(bin_dir / exe)
    create_exe(bin_dir / "starship", "#!/usr/bin/env bash\nif [[ $1 == init && $2 == zsh ]]; then\n  echo 'STARSHIP_INIT'\nfi\n")
    create_git_stub(bin_dir / "git", tmp_path / "git.log")
    create_exe(bin_dir / "hostname", "#!/usr/bin/env bash\necho WORK-LAPTOP.corp.local\n")
    (bin_dir / "bash").symlink_to("/bin/bash")
    (bin_dir / "dirname").symlink_to("/usr/bin/dirname")

    env = os.environ.copy()
    env.update({"OSTYPE": "linux-gnu", "PATH": f"{bin_dir}:/usr/bin:/bin", "HOME": str(tmp_path / 'home')})

    subprocess.run(
        ["/bin/bash", "scripts/install_common.sh", "--host", "work_laptop"],
        cwd=repo,
        check=True,
        env=env,
    )

    install_dotfiles_calls = install_dotfiles_log.read_text(encoding="utf-8").splitlines()
    assert install_dotfiles_calls == ["--host work_laptop"]


def test_install_common_normalizes_detected_hostname_for_host_overlay(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo_dotfiles_normalized"
    repo.mkdir()

    scripts_dir = repo / "scripts"
    helpers_dir = scripts_dir / "helpers"
    helpers_dir.mkdir(parents=True)

    shutil.copy(repo_root / "scripts" / "install_common.sh", scripts_dir / "install_common.sh")

    for path in [scripts_dir / "setup-hooks.sh", helpers_dir / "install_fonts.sh", helpers_dir / "sync_palettes.sh"]:
        path.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        path.chmod(0o755)

    install_dotfiles_log = tmp_path / "install_dotfiles_normalized.log"
    (scripts_dir / "install_dotfiles.sh").write_text(
        f"#!/usr/bin/env bash\nprintf '%s\\n' \"$*\" >> '{install_dotfiles_log}'\n",
        encoding="utf-8",
    )
    (scripts_dir / "install_dotfiles.sh").chmod(0o755)

    (repo / "hosts" / "work_laptop").mkdir(parents=True)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for exe in ["curl", "unzip", "zsh", "tmux", "nvim", "cargo", "stow"]:
        create_exe(bin_dir / exe)
    create_exe(bin_dir / "starship", "#!/usr/bin/env bash\nif [[ $1 == init && $2 == zsh ]]; then\n  echo 'STARSHIP_INIT'\nfi\n")
    create_git_stub(bin_dir / "git", tmp_path / "git_normalized.log")
    create_exe(bin_dir / "hostname", "#!/usr/bin/env bash\necho WORK-LAPTOP.corp.local\n")
    (bin_dir / "bash").symlink_to("/bin/bash")
    (bin_dir / "dirname").symlink_to("/usr/bin/dirname")

    env = os.environ.copy()
    env.update({"OSTYPE": "linux-gnu", "PATH": f"{bin_dir}:/usr/bin:/bin", "HOME": str(tmp_path / 'home')})

    subprocess.run(["/bin/bash", "scripts/install_common.sh"], cwd=repo, check=True, env=env)

    install_dotfiles_calls = install_dotfiles_log.read_text(encoding="utf-8").splitlines()
    assert install_dotfiles_calls == ["--host work_laptop"]


def test_install_common_dry_run_lists_required_rg_and_fd_packages(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo_dry_run"
    repo.mkdir()

    scripts_dir = repo / "scripts"
    shutil.copytree(repo_root / "scripts", scripts_dir)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    create_exe(bin_dir / "apt-get")
    create_exe(bin_dir / "sudo", "#!/usr/bin/env bash\n\"$@\"\n")
    (bin_dir / "bash").symlink_to("/bin/bash")
    (bin_dir / "dirname").symlink_to("/usr/bin/dirname")

    env = os.environ.copy()
    env.update({"OSTYPE": "linux-gnu", "PATH": str(bin_dir)})

    result = subprocess.run(
        ["/bin/bash", "scripts/install_common.sh", "--dry-run"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert "apt-get install -y" in output
    assert "ripgrep" in output
    assert "fd-find" in output
