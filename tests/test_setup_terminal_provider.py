import os
import shutil
import subprocess
from pathlib import Path


def _create_terminal_profile(tmp_path: Path, body: str = "#!/usr/bin/env bash\nexit 0\n") -> Path:
    xdg_config_home = tmp_path / "xdg"
    profile = xdg_config_home / "tino" / "terminal-profile.sh"
    profile.parent.mkdir(parents=True, exist_ok=True)
    profile.write_text(body, encoding="utf-8")
    profile.chmod(0o755)
    return xdg_config_home


def _create_minimal_bin(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    (bin_dir / "dirname").symlink_to("/usr/bin/dirname")
    (bin_dir / "bash").symlink_to("/bin/bash")
    return bin_dir


def test_setup_terminal_provider_fails_when_provider_not_installed(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir(parents=True)
    shutil.copy(repo_root / "scripts" / "setup-terminal-provider.sh", scripts_dir / "setup-terminal-provider.sh")

    xdg_config_home = _create_terminal_profile(tmp_path)
    bin_dir = _create_minimal_bin(tmp_path)

    env = os.environ.copy()
    env.update({"XDG_CONFIG_HOME": str(xdg_config_home), "PATH": str(bin_dir)})

    result = subprocess.run(
        ["/bin/bash", "scripts/setup-terminal-provider.sh", "wezterm"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0
    assert "Error: wezterm is still unavailable after installation attempt." in output
    assert "Terminal provider configured" not in output


def test_setup_terminal_provider_ghostty_renders_via_profile_script(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir(parents=True)
    shutil.copy(repo_root / "scripts" / "setup-terminal-provider.sh", scripts_dir / "setup-terminal-provider.sh")

    setup_ghostty = scripts_dir / "setup-ghostty.sh"
    setup_ghostty.write_text("#!/usr/bin/env bash\nexit 42\n", encoding="utf-8")
    setup_ghostty.chmod(0o755)

    render_log = tmp_path / "render.log"
    xdg_config_home = _create_terminal_profile(
        tmp_path,
        "#!/usr/bin/env bash\n"
        f"echo \"$@\" > '{render_log}'\n",
    )
    bin_dir = _create_minimal_bin(tmp_path)

    env = os.environ.copy()
    env.update({"XDG_CONFIG_HOME": str(xdg_config_home), "PATH": str(bin_dir)})

    result = subprocess.run(
        ["/bin/bash", "scripts/setup-terminal-provider.sh", "ghostty"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    assert render_log.read_text().strip() == "ghostty " + str(repo)
    assert "Terminal provider configured: ghostty" in result.stdout


def test_setup_terminal_provider_windows_terminal_validates_inputs(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    scripts_dir = repo / "scripts"
    windows_terminal_dir = repo / "windows-terminal"
    scripts_dir.mkdir(parents=True)
    windows_terminal_dir.mkdir(parents=True)
    shutil.copy(repo_root / "scripts" / "setup-terminal-provider.sh", scripts_dir / "setup-terminal-provider.sh")
    shutil.copy(repo_root / "windows-terminal" / "settings.base.json", windows_terminal_dir / "settings.base.json")

    xdg_config_home = _create_terminal_profile(tmp_path)
    bin_dir = _create_minimal_bin(tmp_path)

    env = os.environ.copy()
    env.update({"XDG_CONFIG_HOME": str(xdg_config_home), "PATH": str(bin_dir)})

    result = subprocess.run(
        ["/bin/bash", "scripts/setup-terminal-provider.sh", "windows-terminal"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0
    assert "Error: required Windows Terminal input is missing" in output
    assert "Terminal provider configured" not in output


def test_setup_terminal_provider_rejects_unsupported_provider(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir(parents=True)
    shutil.copy(repo_root / "scripts" / "setup-terminal-provider.sh", scripts_dir / "setup-terminal-provider.sh")

    xdg_config_home = _create_terminal_profile(tmp_path)
    bin_dir = _create_minimal_bin(tmp_path)

    env = os.environ.copy()
    env.update({"XDG_CONFIG_HOME": str(xdg_config_home), "PATH": str(bin_dir)})

    result = subprocess.run(
        ["/bin/bash", "scripts/setup-terminal-provider.sh", "bad-term"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0
    assert "Unsupported provider: bad-term" in output
