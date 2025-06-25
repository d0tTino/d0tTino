import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(
    shutil.which("pwsh") is None and shutil.which("powershell") is None,
    reason="requires PowerShell",
)
def test_install_windows_terminal_copies_settings(tmp_path: Path) -> None:
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    env = os.environ.copy()
    env["LOCALAPPDATA"] = str(tmp_path)
    subprocess.run(
        [pwsh, "-NoLogo", "-NoProfile", "-File", "scripts/install-windows-terminal.ps1"],
        check=True,
        env=env,
    )
    dest = (
        tmp_path
        / "Packages"
        / "Microsoft.WindowsTerminal_8wekyb3d8bbwe"
        / "LocalState"
        / "settings.json"
    )
    assert dest.is_file(), "settings.json should be copied"
    expected = Path("windows-terminal/settings.json").read_text(encoding="utf-8")
    assert dest.read_text(encoding="utf-8") == expected
