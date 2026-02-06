import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def create_exe(path, contents="#!/usr/bin/env bash\n"):
    path.write_text(contents)
    path.chmod(0o755)


def test_setup_wsl_symlinks(tmp_path):
    fake_root = tmp_path
    bin_dir = fake_root / "bin"
    usr_local_bin = fake_root / "usr/local/bin"
    bin_dir.mkdir(parents=True)
    usr_local_bin.mkdir(parents=True)

    # Stub commands
    apt_log = fake_root / "apt_history"
    apt_stub = (
        "#!/usr/bin/env bash\n"
        f"echo \"$@\" >> \"{apt_log}\"\n"
        "if [[ $1 == install ]]; then\n"
        f"  touch {bin_dir}/starship {bin_dir}/zoxide {bin_dir}/zsh\n"
        f"  chmod 755 {bin_dir}/starship {bin_dir}/zoxide {bin_dir}/zsh\n"
        "fi\n"
    )
    create_exe(bin_dir / "apt-get", apt_stub)
    create_exe(bin_dir / "sudo", "#!/bin/sh\n\"$@\"\n")
    create_exe(bin_dir / "batcat")
    create_exe(bin_dir / "fdfind")
    create_exe(bin_dir / "getent", "#!/usr/bin/env bash\necho \"$2:x:1000:1000::/home/$2:/bin/bash\"\n")
    chsh_log = fake_root / "chsh_history"
    create_exe(bin_dir / "chsh", f"#!/usr/bin/env bash\necho \"$@\" >> \"{chsh_log}\"\n")

    # ln wrapper that redirects /usr/local/bin to FAKE_ROOT
    ln_script = """#!/usr/bin/env bash
last=${@: -1}
if [[ $last == /usr/local/bin/* && -n $FAKE_ROOT ]]; then
  dest=$FAKE_ROOT$last
  mkdir -p $(dirname "$dest")
  /bin/ln -sf ${@:1:$(($#-1))} "$dest"
else
  /bin/ln "$@"
fi
"""
    create_exe(bin_dir / "ln", ln_script)

    env = os.environ.copy()
    env.update({
        "PATH": f"{bin_dir}:/bin",
        "FAKE_ROOT": str(fake_root),
        "HOME": str(fake_root),
    })

    subprocess.run(
        ["bash", str(REPO_ROOT / "scripts" / "setup-wsl.sh")],
        check=True,
        env=env,
        cwd=tmp_path,
    )

    bat_link = usr_local_bin / "bat"
    fd_link = usr_local_bin / "fd"
    assert bat_link.is_symlink()
    assert os.readlink(bat_link) == str(bin_dir / "batcat")
    assert fd_link.is_symlink()
    assert os.readlink(fd_link) == str(bin_dir / "fdfind")

    lines = apt_log.read_text().splitlines()
    assert lines[0] == "update"
    install_args = lines[1].split()
    assert install_args[:2] == ["install", "-y"]
    required = [
        "git",
        "ripgrep",
        "fd-find",
        "bat",
        "fzf",
        "build-essential",
        "starship",
        "zoxide",
        "zsh",
    ]
    for pkg in required:
        assert pkg in install_args

    assert chsh_log.read_text().strip() == f"-s {bin_dir / 'zsh'}"
    assert not (fake_root / ".bashrc").exists()


def test_setup_wsl_skips_chsh_when_zsh_is_already_default(tmp_path):
    fake_root = tmp_path
    bin_dir = fake_root / "bin"
    bin_dir.mkdir(parents=True)

    create_exe(bin_dir / "apt-get", "#!/usr/bin/env bash\nexit 0\n")
    create_exe(bin_dir / "sudo", "#!/bin/sh\n\"$@\"\n")
    create_exe(bin_dir / "curl", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "starship", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "zoxide", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "zsh", "#!/bin/sh\nexit 0\n")
    create_exe(
        bin_dir / "getent",
        f"#!/usr/bin/env bash\necho \"$2:x:1000:1000::/home/$2:{bin_dir / 'zsh'}\"\n",
    )
    chsh_log = fake_root / "chsh_history"
    create_exe(bin_dir / "chsh", f"#!/usr/bin/env bash\necho \"$@\" >> \"{chsh_log}\"\n")

    env = os.environ.copy()
    env.update({
        "PATH": f"{bin_dir}:/bin",
        "HOME": str(fake_root),
    })

    subprocess.run(
        ["/bin/bash", str(REPO_ROOT / "scripts" / "setup-wsl.sh")],
        check=True,
        env=env,
        cwd=tmp_path,
    )

    assert not chsh_log.exists()


def test_setup_wsl_requires_sudo(tmp_path):
    fake_root = tmp_path
    bin_dir = fake_root / "bin"
    bin_dir.mkdir(parents=True)

    # Stub commands so the script doesn't try to run the real ones
    create_exe(bin_dir / "apt-get", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "curl", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "starship", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "zoxide", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "zsh", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "id", "#!/bin/sh\necho 1000\n")

    (bin_dir / "grep").symlink_to("/usr/bin/grep")
    (bin_dir / "dirname").symlink_to("/usr/bin/dirname")
    (bin_dir / "cat").symlink_to("/bin/cat")
    env = os.environ.copy()
    env.update({
        "PATH": str(bin_dir),
    })

    result = subprocess.run(
        ["/bin/bash", str(REPO_ROOT / "scripts" / "setup-wsl.sh")],
        env=env,
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )

    assert result.returncode != 0
    assert "sudo is required" in result.stderr


def test_setup_wsl_root_without_sudo(tmp_path):
    fake_root = tmp_path
    bin_dir = fake_root / "bin"
    bin_dir.mkdir(parents=True)

    create_exe(bin_dir / "apt-get", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "curl", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "starship", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "zoxide", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "zsh", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "id", "#!/bin/sh\necho 0\n")

    (bin_dir / "grep").symlink_to("/usr/bin/grep")
    (bin_dir / "dirname").symlink_to("/usr/bin/dirname")
    (bin_dir / "cat").symlink_to("/bin/cat")
    env = os.environ.copy()
    env.update({
        "PATH": str(bin_dir),
    })

    subprocess.run(
        ["/bin/bash", str(REPO_ROOT / "scripts" / "setup-wsl.sh")],
        check=True,
        env=env,
        cwd=tmp_path,
    )


def test_setup_wsl_requires_apt_get(tmp_path):
    fake_root = tmp_path
    bin_dir = fake_root / "bin"
    bin_dir.mkdir(parents=True)

    create_exe(bin_dir / "curl", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "starship", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "zoxide", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "zsh", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "id", "#!/bin/sh\necho 0\n")

    (bin_dir / "grep").symlink_to("/usr/bin/grep")
    (bin_dir / "dirname").symlink_to("/usr/bin/dirname")
    (bin_dir / "cat").symlink_to("/bin/cat")

    env = os.environ.copy()
    env.update({
        "PATH": str(bin_dir),
    })

    result = subprocess.run(
        [
            "/bin/bash",
            str(REPO_ROOT / "scripts" / "setup-wsl.sh"),
        ],
        env=env,
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )

    assert result.returncode != 0
    assert "apt-get is required" in result.stderr


def test_setup_wsl_starship_install_failure(tmp_path):
    fake_root = tmp_path
    bin_dir = fake_root / "bin"
    bin_dir.mkdir(parents=True)

    create_exe(bin_dir / "apt-get", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "sudo", "#!/bin/sh\n\"$@\"\n")
    create_exe(bin_dir / "curl", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "zsh", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "id", "#!/bin/sh\necho 0\n")

    (bin_dir / "grep").symlink_to("/usr/bin/grep")
    (bin_dir / "dirname").symlink_to("/usr/bin/dirname")
    (bin_dir / "cat").symlink_to("/bin/cat")

    env = os.environ.copy()
    env.update({
        "PATH": f"{bin_dir}:/bin",
        "HOME": str(fake_root),
    })

    result = subprocess.run(
        [
            "/bin/bash",
            str(REPO_ROOT / "scripts" / "setup-wsl.sh"),
        ],
        env=env,
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )

    assert result.returncode != 0
    assert "starship installation failed" in result.stderr


def test_setup_wsl_zoxide_install_failure(tmp_path):
    fake_root = tmp_path
    bin_dir = fake_root / "bin"
    bin_dir.mkdir(parents=True)

    create_exe(bin_dir / "apt-get", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "sudo", "#!/bin/sh\n\"$@\"\n")
    create_exe(bin_dir / "curl", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "starship", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "zsh", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "id", "#!/bin/sh\necho 0\n")

    (bin_dir / "grep").symlink_to("/usr/bin/grep")
    (bin_dir / "dirname").symlink_to("/usr/bin/dirname")
    (bin_dir / "cat").symlink_to("/bin/cat")

    env = os.environ.copy()
    env.update({
        "PATH": f"{bin_dir}:/bin",
        "HOME": str(fake_root),
    })

    result = subprocess.run(
        [
            "/bin/bash",
            str(REPO_ROOT / "scripts" / "setup-wsl.sh"),
        ],
        env=env,
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )

    assert result.returncode != 0
    assert "zoxide installation failed" in result.stderr
