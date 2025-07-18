import os
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("requests")


def create_exe(path: Path, contents: str = "#!/usr/bin/env bash\n") -> None:
    path.write_text(contents)
    path.chmod(0o755)


def test_provision_vm_wsl_import(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_file = tmp_path / "wsl.log"
    ntfy_log = tmp_path / "ntfy.log"
    create_exe(bin_dir / "wsl", f"#!/usr/bin/env bash\necho \"$@\" > '{log_file}'\n")
    create_exe(bin_dir / "ntfy", f"#!/usr/bin/env bash\necho \"$@\" > '{ntfy_log}'\n")

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    subprocess.run(
        [
            "python",
            "scripts/provision_vm.py",
            "wsl",
            "--name",
            "Dev",
            "--rootfs",
            str(tmp_path / "ubuntu.tar"),
            "--target",
            str(tmp_path / "dev"),
            "--notify",
        ],
        check=True,
        env=env,
    )

    args = log_file.read_text().strip().split()
    assert "--import" in args
    assert "Dev" in args
    assert str(tmp_path / "dev") in args
    assert str(tmp_path / "ubuntu.tar") in args
    assert "send" in ntfy_log.read_text()


def test_provision_vm_hyperv(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    ps_log = tmp_path / "ps.log"
    ntfy_log = tmp_path / "ntfy.log"
    create_exe(bin_dir / "pwsh", f"#!/usr/bin/env bash\necho \"$@\" > '{ps_log}'\n")
    create_exe(bin_dir / "ntfy", f"#!/usr/bin/env bash\necho \"$@\" > '{ntfy_log}'\n")

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    subprocess.run(
        [
            "python",
            "scripts/provision_vm.py",
            "hyperv",
            "--name",
            "TestVM",
            "--quick",
            "--notify",
        ],
        check=True,
        env=env,
    )

    contents = ps_log.read_text()
    assert "create-hyperv-vm.ps1" in contents
    assert "-Name" in contents and "TestVM" in contents
    assert "send" in ntfy_log.read_text()

