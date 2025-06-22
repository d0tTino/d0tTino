import os
import subprocess
from pathlib import Path

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
    create_exe(bin_dir / "apt-get", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "sudo", "#!/usr/bin/env bash\n\"$@\"\n")
    create_exe(bin_dir / "batcat")
    create_exe(bin_dir / "fdfind")
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
        "PATH": f"{bin_dir}:{env['PATH']}",
        "FAKE_ROOT": str(fake_root),
    })

    subprocess.run(["bash", "scripts/setup-wsl.sh"], check=True, env=env)

    bat_link = usr_local_bin / "bat"
    fd_link = usr_local_bin / "fd"
    assert bat_link.is_symlink()
    assert os.readlink(bat_link) == str(bin_dir / "batcat")
    assert fd_link.is_symlink()
    assert os.readlink(fd_link) == str(bin_dir / "fdfind")


def test_setup_wsl_requires_sudo(tmp_path):
    fake_root = tmp_path
    bin_dir = fake_root / "bin"
    bin_dir.mkdir(parents=True)

    # Stub commands so the script doesn't try to run the real ones
    create_exe(bin_dir / "apt-get", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "curl", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "starship", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "zoxide", "#!/bin/sh\nexit 0\n")
    create_exe(bin_dir / "id", "#!/bin/sh\necho 1000\n")

    env = os.environ.copy()
    env.update({
        "PATH": str(bin_dir),
    })

    result = subprocess.run(
        ["/bin/bash", "scripts/setup-wsl.sh"],
        env=env,
        capture_output=True,
        text=True,
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
    create_exe(bin_dir / "id", "#!/bin/sh\necho 0\n")

    env = os.environ.copy()
    env.update({
        "PATH": str(bin_dir),
    })

    subprocess.run(["/bin/bash", "scripts/setup-wsl.sh"], check=True, env=env)
   
