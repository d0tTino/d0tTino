import os
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def create_exe(path: Path, contents: str = "#!/usr/bin/env bash\n") -> None:
    path.write_text(contents)
    path.chmod(0o755)


def test_setup_ghostty_requires_install_path(tmp_path: Path) -> None:
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
    assert "unable to install Ghostty" in result.stderr


def test_setup_ghostty_skips_install_when_preinstalled(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    shutil.copy(REPO_ROOT / "scripts" / "setup-ghostty.sh", scripts_dir / "setup-ghostty.sh")
    (scripts_dir / "setup-terminal-provider.sh").write_text("#!/usr/bin/env bash\nexit 0\n")
    (scripts_dir / "setup-terminal-provider.sh").chmod(0o755)
    shutil.copytree(REPO_ROOT / "dotfiles", repo / "dotfiles")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    cargo_log = tmp_path / "cargo.log"
    create_exe(bin_dir / "cargo", f"#!/usr/bin/env bash\necho \"$@\" > '{cargo_log}'\n")
    create_exe(bin_dir / "ghostty", "#!/usr/bin/env bash\n")

    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}:{env['PATH']}",
            "HOME": str(tmp_path),
            "XDG_CONFIG_HOME": str(tmp_path / "config"),
            "OSTYPE": "unknown",
        }
    )

    result = subprocess.run(
        ["/bin/bash", "scripts/setup-ghostty.sh"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "skipping install" in result.stdout.lower()
    assert not cargo_log.exists()


def test_setup_ghostty_installs_and_renders(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    shutil.copy(REPO_ROOT / "scripts" / "setup-ghostty.sh", scripts_dir / "setup-ghostty.sh")
    provider_log = tmp_path / "provider.log"
    (scripts_dir / "setup-terminal-provider.sh").write_text(
        "#!/usr/bin/env bash\n"
        f"echo \"$@\" > '{provider_log}'\n"
    )
    (scripts_dir / "setup-terminal-provider.sh").chmod(0o755)
    shutil.copytree(REPO_ROOT / "dotfiles", repo / "dotfiles")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    cargo_log = tmp_path / "cargo.log"
    create_exe(
        bin_dir / "cargo",
        f"#!/usr/bin/env bash\necho \"$@\" > '{cargo_log}'\ncat > '{bin_dir}/ghostty' <<'EOF'\n#!/usr/bin/env bash\nEOF\nchmod +x '{bin_dir}/ghostty'\n",
    )

    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}:{env['PATH']}",
            "HOME": str(tmp_path),
            "XDG_CONFIG_HOME": str(tmp_path / "config"),
            "OSTYPE": "unknown",
        }
    )

    subprocess.run(
        ["/bin/bash", "scripts/setup-ghostty.sh"],
        cwd=repo,
        env=env,
        check=True,
    )

    assert cargo_log.read_text().strip() == "install --locked ghostty"
    assert provider_log.read_text().strip() == "ghostty"


def test_setup_ghostty_installs_with_package_manager_without_cargo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    shutil.copy(REPO_ROOT / "scripts" / "setup-ghostty.sh", scripts_dir / "setup-ghostty.sh")
    (scripts_dir / "setup-terminal-provider.sh").write_text("#!/usr/bin/env bash\nexit 0\n")
    (scripts_dir / "setup-terminal-provider.sh").chmod(0o755)
    shutil.copytree(REPO_ROOT / "dotfiles", repo / "dotfiles")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    apt_log = tmp_path / "apt.log"
    create_exe(
        bin_dir / "apt-get",
        (
            "#!/bin/bash\n"
            f"echo \"$@\" >> '{apt_log}'\n"
            "if [[ \"$1\" == \"install\" ]]; then\n"
            "  cat > \"$(dirname \"$0\")/ghostty\" <<'EOF'\n"
            "#!/bin/bash\n"
            "EOF\n"
            "  chmod +x \"$(dirname \"$0\")/ghostty\"\n"
            "fi\n"
        ),
    )

    env = {
        "PATH": f"{bin_dir}:/usr/bin:/bin",
        "HOME": str(tmp_path),
        "XDG_CONFIG_HOME": str(tmp_path / "config"),
        "OSTYPE": "linux",
    }

    result = subprocess.run(
        ["/bin/bash", "scripts/setup-ghostty.sh"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    apt_calls = apt_log.read_text().splitlines()
    assert apt_calls == ["update", "install -y ghostty"]
    assert "native package manager" in result.stdout


def test_setup_ghostty_delegates_rendering_to_terminal_provider(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    shutil.copy(REPO_ROOT / "scripts" / "setup-ghostty.sh", scripts_dir / "setup-ghostty.sh")
    provider_log = tmp_path / "provider.log"
    (scripts_dir / "setup-terminal-provider.sh").write_text(
        "#!/usr/bin/env bash\n"
        f"echo \"$@\" >> '{provider_log}'\n"
    )
    (scripts_dir / "setup-terminal-provider.sh").chmod(0o755)
    shutil.copytree(REPO_ROOT / "dotfiles", repo / "dotfiles")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    create_exe(bin_dir / "cargo", "#!/usr/bin/env bash\n")
    create_exe(bin_dir / "ghostty", "#!/usr/bin/env bash\n")

    config_home = tmp_path / "config"
    tino_dir = config_home / "tino"
    tino_dir.mkdir(parents=True)
    (tino_dir / "terminal-defaults.sh").write_text(
        "TINO_TERMINAL_OPACITY=0.91\n"
        "TINO_TERMINAL_FPS=120\n"
            "TINO_TERMINAL_EFFECTS=scanlines.glsl\n"
    )
    (tino_dir / "host-overrides.sh").write_text(
        "TINO_TERMINAL_OPACITY=0.73\nTINO_TERMINAL_FPS=144\n"
    )

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

    assert provider_log.read_text().splitlines() == ["ghostty"]

    second = subprocess.run(
        ["/bin/bash", "scripts/setup-ghostty.sh"],
        cwd=repo,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    assert provider_log.read_text().splitlines() == ["ghostty", "ghostty"]


def test_managed_ghostty_template_has_required_keys() -> None:
    template_path = REPO_ROOT / "dotfiles" / "terminal" / ".config" / "tino" / "ghostty.toml.tmpl"
    contents = template_path.read_text()

    required = [
        "font-family = ",
        "font-size = ",
        "background-opacity = __BACKGROUND_OPACITY__",
        "custom-shader-animation-max-fps = __MAX_FPS__",
        "__CUSTOM_SHADER_LINE__",
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

    assert 'canonical_template="$repo_root/dotfiles/terminal/.config/tino/ghostty.toml.tmpl"' in script_contents


def test_setup_script_does_not_embed_ghostty_renderer() -> None:
    script_path = REPO_ROOT / "scripts" / "setup-ghostty.sh"
    script_contents = script_path.read_text()

    assert "render_ghostty_config" not in script_contents
    assert "__CUSTOM_SHADER_LINE__" not in script_contents
