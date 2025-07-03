import os
import shutil
import subprocess
from pathlib import Path

def create_exe(path: Path, contents: str = "#!/usr/bin/env bash\n") -> None:
    path.write_text(contents)
    path.chmod(0o755)


def test_setup_ghostty_requires_cargo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    shutil.copy(Path("scripts/setup-ghostty.sh"), scripts_dir / "setup-ghostty.sh")

    env = {
        "PATH": str(tmp_path / "bin"),
        "HOME": str(tmp_path),
        "XDG_CONFIG_HOME": str(tmp_path / "config"),
    }
    (tmp_path / "bin").mkdir()

    result = subprocess.run(
        ["/bin/bash", "scripts/setup-ghostty.sh"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "cargo is required" in result.stderr


def test_setup_ghostty_installs_and_copies(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    shutil.copy(Path("scripts/setup-ghostty.sh"), scripts_dir / "setup-ghostty.sh")
    shutil.copytree(Path("dotfiles"), repo / "dotfiles")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    cargo_log = tmp_path / "cargo.log"
    create_exe(bin_dir / "cargo", f"#!/usr/bin/env bash\necho \"$@\" > '{cargo_log}'\n")

    env = os.environ.copy()
    env.update({
        "PATH": f"{bin_dir}:{env['PATH']}",
        "HOME": str(tmp_path),
        "XDG_CONFIG_HOME": str(tmp_path / "config"),
    })

    subprocess.run(
        ["/bin/bash", "scripts/setup-ghostty.sh"],
        cwd=repo,
        env=env,
        check=True,
    )

    assert cargo_log.read_text().strip() == "install --locked ghostty"
    config_file = Path(env["XDG_CONFIG_HOME"]) / "ghostty/ghostty.toml"
    assert config_file.exists()
