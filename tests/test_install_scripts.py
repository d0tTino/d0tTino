import os
import shutil
import subprocess
from pathlib import Path

import pytest


# Test syntax check (dry run) for install_common.sh using bash -n

def test_install_common_sh_dry_run() -> None:
    script = Path('scripts/install_common.sh')
    subprocess.run(['/bin/bash', '-n', str(script)], check=True)


# Test syntax check for install.ps1 using PowerShell parser
@pytest.mark.skipif(shutil.which('pwsh') is None and shutil.which('powershell') is None,
                    reason='requires PowerShell')
def test_install_ps1_dry_run() -> None:
    pwsh = shutil.which('pwsh') or shutil.which('powershell')
    script = Path('scripts/install.ps1').resolve()
    command = f"[System.Management.Automation.Language.Parser]::ParseFile('{script}',[ref]\$null,[ref]\$null) | Out-Null"
    subprocess.run([pwsh, '-NoLogo', '-NoProfile', '-Command', command], check=True)
