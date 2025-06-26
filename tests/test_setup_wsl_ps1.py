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
def test_setup_wsl_ps1_invokes_wsl(tmp_path: Path) -> None:
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_file = tmp_path / "wsl.log"
    create_exe(bin_dir / "wsl", f"#!/usr/bin/env bash\necho \"$@\" > '{log_file}'\n")

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    subprocess.run(
        [
            pwsh,
            "-NoLogo",
            "-NoProfile",
            "-Command",
            (
                "Set-Variable -Name IsWindows -Value $true -Force; "
                f"& '{Path('scripts/setup-wsl.ps1')}'"
            ),
        ],
        check=True,
        env=env,
    )

    args = log_file.read_text().strip().split()
    assert args and args[0] == "bash"
    assert args[1].replace('\\', '/').endswith('scripts/setup-wsl.sh')
