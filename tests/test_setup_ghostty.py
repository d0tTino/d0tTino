import os
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def create_exe(path: Path, contents: str = "#!/usr/bin/env bash\n") -> None:
    path.write_text(contents)
    path.chmod(0o755)


def test_setup_ghostty_requires_cargo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    shutil.copy(REPO_ROOT / "scripts" / "setup-ghostty.sh", scripts_dir / "setup-ghostty.sh")

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


def test_setup_ghostty_installs_and_renders(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    shutil.copy(REPO_ROOT / "scripts" / "setup-ghostty.sh", scripts_dir / "setup-ghostty.sh")
    shutil.copytree(REPO_ROOT / "dotfiles", repo / "dotfiles")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    cargo_log = tmp_path / "cargo.log"
    create_exe(bin_dir / "cargo", f"#!/usr/bin/env bash\necho \"$@\" > '{cargo_log}'\n")

    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}:{env['PATH']}",
            "HOME": str(tmp_path),
            "XDG_CONFIG_HOME": str(tmp_path / "config"),
        }
    )

    subprocess.run(
        ["/bin/bash", "scripts/setup-ghostty.sh"],
        cwd=repo,
        env=env,
        check=True,
    )

    assert cargo_log.read_text().strip() == "install --locked ghostty"
    config_file = Path(env["XDG_CONFIG_HOME"]) / "ghostty/ghostty.toml"
    assert config_file.exists()
    config_contents = config_file.read_text()
    assert "background-opacity = 0.92" in config_contents
    assert 'custom-shader = "crt"' in config_contents


def test_setup_ghostty_renders_host_overrides(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    shutil.copy(REPO_ROOT / "scripts" / "setup-ghostty.sh", scripts_dir / "setup-ghostty.sh")
    shutil.copytree(REPO_ROOT / "dotfiles", repo / "dotfiles")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    create_exe(bin_dir / "cargo", "#!/usr/bin/env bash\n")
    create_exe(bin_dir / "ghostty", "#!/usr/bin/env bash\n")

    config_home = tmp_path / "config"
    tino_dir = config_home / "tino"
    tino_dir.mkdir(parents=True)
    (tino_dir / "terminal-defaults.sh").write_text(
        "TERMINAL_OPACITY=0.91\nTERMINAL_FPS=120\nTERMINAL_EFFECTS='\"scanlines\"'\n"
    )
    (tino_dir / "host-overrides.sh").write_text("TERMINAL_OPACITY=0.73\nTERMINAL_FPS=144\n")

    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}:{env['PATH']}",
            "HOME": str(tmp_path),
            "XDG_CONFIG_HOME": str(config_home),
        }
    )

    first = subprocess.run(
        ["/bin/bash", "scripts/setup-ghostty.sh"],
        cwd=repo,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    config_file = config_home / "ghostty" / "ghostty.toml"
    config_contents = config_file.read_text()
    assert "background-opacity = 0.73" in config_contents
    assert "custom-shader-animation-max-fps = 144" in config_contents
    assert 'custom-shader = "scanlines"' in config_contents
    assert "Configuration rendered" in first.stdout

    second = subprocess.run(
        ["/bin/bash", "scripts/setup-ghostty.sh"],
        cwd=repo,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Configuration already up to date" in second.stdout


def test_managed_ghostty_template_has_required_keys() -> None:
    template_path = REPO_ROOT / "dotfiles" / "ghostty" / "ghostty.toml.tmpl"
    contents = template_path.read_text()

    required = [
        "font-family = ",
        "font-size = ",
        "background-opacity = __BACKGROUND_OPACITY__",
        "custom-shader-animation-max-fps = __MAX_FPS__",
        "custom-shader = __EFFECTS__",
        "cursor-style = ",
        "window-title = ",
    ]
    for key in required:
        assert key in contents

    palette_entries = [line for line in contents.splitlines() if line.startswith("palette = ")]
    assert len(palette_entries) >= 16


def test_setup_script_uses_canonical_template_path() -> None:
    script_path = REPO_ROOT / "scripts" / "setup-ghostty.sh"
    script_contents = script_path.read_text()

    assert 'canonical_template="$repo_root/dotfiles/ghostty/ghostty.toml.tmpl"' in script_contents
    assert "dotfiles/terminal/.config/ghostty/ghostty.toml" not in script_contents
