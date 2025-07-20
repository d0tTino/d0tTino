import os
import subprocess
import shutil
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def create_exe(path: Path, contents: str = "#!/usr/bin/env bash\n") -> None:
    path.write_text(contents)
    path.chmod(0o755)


@pytest.mark.skipif(
    shutil.which("pwsh") is None and shutil.which("powershell") is None,
    reason="requires PowerShell",
)
def test_setup_winget_installs_packages(tmp_path: Path) -> None:
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
        [
            pwsh,
            "-NoLogo",
            "-NoProfile",
            "-Command",
            (
                "Set-Variable -Name IsWindows -Value $true -Force; "
                f"& '{REPO_ROOT / 'scripts' / 'setup-winget.ps1'}'"
            ),
        ],
        check=True,
        env=env,
        cwd=tmp_path,
    )
    lines = winget_log.read_text().splitlines()
    ids = [line.split()[line.split().index("--id") + 1] for line in lines]
    assert ids == [
        "ajeetdsouza.zoxide",
        "junegunn.fzf",
        "sharkdp.bat",
        "dandavison.delta",
        "Starship.Starship",
        "Microsoft.WindowsTerminal",
        "OpenSSH.Client",
    ]
