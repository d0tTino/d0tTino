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
def test_create_hyperv_vm_invokes_new_vm(tmp_path: Path) -> None:
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_file = tmp_path / "vm.log"
    create_exe(bin_dir / "New-VM", f"#!/usr/bin/env bash\necho \"$@\" > '{log_file}'\n")

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
                f"& '{Path('scripts/create-hyperv-vm.ps1')}' -Name TestVM"
            ),
        ],
        check=True,
        env=env,
    )

    assert log_file.read_text().strip()


@pytest.mark.skipif(
    shutil.which("pwsh") is None and shutil.which("powershell") is None,
    reason="requires PowerShell",
)
def test_create_hyperv_vm_parses_iso_and_cloudinit(tmp_path: Path) -> None:
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    dvd_log = tmp_path / "dvd.log"
    request_log = tmp_path / "request.log"
    create_exe(bin_dir / "New-VM")
    create_exe(bin_dir / "Add-VMDvdDrive", f"#!/usr/bin/env bash\necho \"$@\" >> '{dvd_log}'\n")
    create_exe(
        bin_dir / "Invoke-WebRequest",
        (
            "#!/usr/bin/env bash\n" +
            f"echo \"$@\" > '{request_log}'\n" +
            f"touch '{tmp_path / 'os.iso'}'\n"
        ),
    )

    cloud_iso = tmp_path / "seed.iso"
    cloud_iso.write_text("")

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
                f"& '{Path('scripts/create-hyperv-vm.ps1')}' -Name TestVM "
                f"-IsoUrl http://example.com/os.iso -CloudInit {cloud_iso}"
            ),
        ],
        check=True,
        env=env,
    )

    assert "http://example.com/os.iso" in request_log.read_text()
    lines = dvd_log.read_text().splitlines()
    assert any(str(cloud_iso) in line for line in lines)

