import os
import subprocess
import shutil
from pathlib import Path

import pytest


def create_exe(path: Path, contents: str = "#!/usr/bin/env bash\n") -> None:
    path.write_text(contents)
    path.chmod(0o755)


@pytest.mark.skipif(shutil.which("bash") is None, reason="requires bash")
def test_setup_screenshot_env_apt(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    apt_log = tmp_path / "apt.log"
    create_exe(
        bin_dir / "apt-get",
        f"#!/usr/bin/env bash\necho \"$@\" >> '{apt_log}'\n",
    )
    create_exe(bin_dir / "sudo", "#!/usr/bin/env bash\n\"$@\"\n")
    create_exe(bin_dir / "wget", "#!/usr/bin/env bash\n: > $2\n")
    create_exe(bin_dir / "dpkg", "#!/usr/bin/env bash\n:")
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    subprocess.run(["/bin/bash", "scripts/setup-screenshot-env.sh"], check=True, env=env)
    lines = apt_log.read_text().splitlines()
    assert lines and lines[0] == "update"
    assert any("install" in line for line in lines)
    assert any("nushell" in line for line in lines)


@pytest.mark.skipif(shutil.which("bash") is None, reason="requires bash")
def test_setup_screenshot_env_pacman(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    pac_log = tmp_path / "pacman.log"
    create_exe(
        bin_dir / "pacman",
        f"#!/usr/bin/env bash\necho \"$@\" >> '{pac_log}'\n",
    )
    create_exe(bin_dir / "sudo", "#!/usr/bin/env bash\n\"$@\"\n")
    create_exe(bin_dir / "uname", "#!/usr/bin/env bash\necho Linux\n")
    (bin_dir / "bash").symlink_to("/bin/bash")
    env = os.environ.copy()
    env["PATH"] = str(bin_dir)
    subprocess.run(["/bin/bash", "scripts/setup-screenshot-env.sh"], check=True, env=env)
    lines = pac_log.read_text().splitlines()
    assert lines and lines[0].startswith("-Sy")
    assert any("nushell" in line for line in lines)


@pytest.mark.skipif(shutil.which("bash") is None, reason="requires bash")
def test_setup_screenshot_env_brew(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    brew_log = tmp_path / "brew.log"
    create_exe(
        bin_dir / "brew",
        f"#!/usr/bin/env bash\necho \"$@\" >> '{brew_log}'\n",
    )
    create_exe(bin_dir / "uname", "#!/usr/bin/env bash\necho Darwin\n")
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    subprocess.run(["/bin/bash", "scripts/setup-screenshot-env.sh"], check=True, env=env)
    lines = brew_log.read_text().splitlines()
    assert any("install" in line for line in lines)
    assert any("nushell" in line for line in lines)
    assert any("zed" in line.lower() for line in lines)


@pytest.mark.skipif(
    shutil.which("pwsh") is None and shutil.which("powershell") is None,
    reason="requires PowerShell",
)
def test_setup_screenshot_env_ps1(tmp_path: Path) -> None:
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    winget_log = tmp_path / "winget.log"
    create_exe(
        bin_dir / "winget",
        f"#!/usr/bin/env bash\necho \"$@\" >> '{winget_log}'\n",
    )
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    subprocess.run(
        [pwsh, "-NoLogo", "-NoProfile", "-File", "scripts/setup-screenshot-env.ps1"],
        check=True,
        env=env,
    )
    content = winget_log.read_text().splitlines()
    assert content, "winget should be invoked"
    assert any("NushellTeam.Nushell" in line for line in content)
    assert any("ZedIndustries.Zed" in line for line in content)
