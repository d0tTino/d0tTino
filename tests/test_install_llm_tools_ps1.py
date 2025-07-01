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
def test_install_llm_tools_uses_pipx(tmp_path: Path) -> None:
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    pipx_log = tmp_path / "pipx.log"
    ollama_log = tmp_path / "ollama.log"
    create_exe(bin_dir / "pipx", f"#!/usr/bin/env bash\necho \"$@\" > '{pipx_log}'\n")
    create_exe(bin_dir / "ollama", f"#!/usr/bin/env bash\necho \"$@\" > '{ollama_log}'\n")

    env = os.environ.copy()
    env["PATH"] = str(bin_dir)
    subprocess.run(
        [
            pwsh,
            "-NoLogo",
            "-NoProfile",
            "-Command",
            (
                "Set-Variable -Name IsWindows -Value $true -Force; "
                f"& '{Path('scripts/install-llm-tools.ps1')}'"
            ),
        ],
        check=True,
        env=env,
    )

    assert pipx_log.read_text().strip() == "install gemini-cli"
    assert ollama_log.read_text().strip() == "pull llama3"


@pytest.mark.skipif(
    shutil.which("pwsh") is None and shutil.which("powershell") is None,
    reason="requires PowerShell",
)
def test_install_llm_tools_uses_pip(tmp_path: Path) -> None:
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    pip_log = tmp_path / "pip.log"
    ollama_log = tmp_path / "ollama.log"
    create_exe(bin_dir / "pip", f"#!/usr/bin/env bash\necho \"$@\" > '{pip_log}'\n")
    create_exe(bin_dir / "ollama", f"#!/usr/bin/env bash\necho \"$@\" > '{ollama_log}'\n")

    env = os.environ.copy()
    env["PATH"] = str(bin_dir)
    subprocess.run(
        [
            pwsh,
            "-NoLogo",
            "-NoProfile",
            "-Command",
            (
                "Set-Variable -Name IsWindows -Value $true -Force; "
                f"& '{Path('scripts/install-llm-tools.ps1')}'"
            ),
        ],
        check=True,
        env=env,
    )

    assert pip_log.read_text().strip() == "install --user gemini-cli"
    assert ollama_log.read_text().strip() == "pull llama3"

