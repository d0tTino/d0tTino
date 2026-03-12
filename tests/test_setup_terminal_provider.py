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


def _create_minimal_bin(tmp_path: Path, *, include_kitty: bool = False) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    (bin_dir / "dirname").symlink_to("/usr/bin/dirname")
    (bin_dir / "bash").symlink_to("/bin/bash")

    for optional_tool in ("mkdir", "python", "python3", "rg"):
        tool_path = shutil.which(optional_tool)
        if tool_path:
            (bin_dir / optional_tool).symlink_to(tool_path)

    if include_kitty:
        kitty = bin_dir / "kitty"
        kitty.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        kitty.chmod(0o755)

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


def test_setup_terminal_provider_applies_same_strictness_for_ghostty(tmp_path: Path) -> None:
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
        ["/bin/bash", "scripts/setup-terminal-provider.sh", "ghostty"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0
    assert "Error: ghostty is still unavailable after installation attempt." in output
    assert "Terminal provider configured" not in output


def test_setup_terminal_provider_ghostty_renders_via_profile_script_in_non_strict_mode(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir(parents=True)
    shutil.copy(repo_root / "scripts" / "setup-terminal-provider.sh", scripts_dir / "setup-terminal-provider.sh")

    render_log = tmp_path / "render.log"
    xdg_config_home = _create_terminal_profile(
        tmp_path,
        "#!/usr/bin/env bash\n"
        f"echo \"$@\" > '{render_log}'\n",
    )
    bin_dir = _create_minimal_bin(tmp_path)

    env = os.environ.copy()
    env.update({"XDG_CONFIG_HOME": str(xdg_config_home), "PATH": str(bin_dir), "TINO_TERMINAL_STRICT": "0"})

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


def test_setup_terminal_provider_falls_back_to_first_available_provider(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir(parents=True)
    shutil.copy(repo_root / "scripts" / "setup-terminal-provider.sh", scripts_dir / "setup-terminal-provider.sh")

    render_log = tmp_path / "render.log"
    xdg_config_home = _create_terminal_profile(
        tmp_path,
        "#!/usr/bin/env bash\n"
        f"echo \"$@\" > '{render_log}'\n",
    )
    bin_dir = _create_minimal_bin(tmp_path, include_kitty=True)

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

    output = f"{result.stdout}\n{result.stderr}"
    assert "using fallback 'kitty'" in output
    assert render_log.read_text().strip() == "kitty " + str(repo)
    assert "Terminal provider configured: kitty" in result.stdout


def test_setup_terminal_provider_non_strict_continues_when_no_provider_available(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir(parents=True)
    shutil.copy(repo_root / "scripts" / "setup-terminal-provider.sh", scripts_dir / "setup-terminal-provider.sh")

    render_log = tmp_path / "render.log"
    xdg_config_home = _create_terminal_profile(
        tmp_path,
        "#!/usr/bin/env bash\n"
        f"echo \"$@\" > '{render_log}'\n",
    )
    bin_dir = _create_minimal_bin(tmp_path)

    env = os.environ.copy()
    env.update({"XDG_CONFIG_HOME": str(xdg_config_home), "PATH": str(bin_dir), "TINO_TERMINAL_STRICT": "0"})

    result = subprocess.run(
        ["/bin/bash", "scripts/setup-terminal-provider.sh", "wezterm"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert "Warning: wezterm is still unavailable after installation attempt; continuing" in output
    assert render_log.read_text().strip() == "wezterm " + str(repo)
    assert "Terminal provider configured: wezterm" in result.stdout



def test_setup_terminal_provider_uses_preference_env_for_fallback_order(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir(parents=True)
    shutil.copy(repo_root / "scripts" / "setup-terminal-provider.sh", scripts_dir / "setup-terminal-provider.sh")

    render_log = tmp_path / "render.log"
    xdg_config_home = _create_terminal_profile(
        tmp_path,
        "#!/usr/bin/env bash\n"
        "if [[ ${1:-} == '--provider-preferences' ]]; then\n"
        "  echo alacritty\n"
        "  echo kitty\n"
        "  exit 0\n"
        "fi\n"
        f"echo \"$@\" > '{render_log}'\n",
    )
    bin_dir = _create_minimal_bin(tmp_path, include_kitty=True)
    alacritty = bin_dir / "alacritty"
    alacritty.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    alacritty.chmod(0o755)

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

    assert render_log.read_text().strip() == "alacritty " + str(repo)
    assert "Terminal provider configured: alacritty" in result.stdout


def test_setup_terminal_provider_persists_fallback_provider_when_enabled(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir(parents=True)
    shutil.copy(repo_root / "scripts" / "setup-terminal-provider.sh", scripts_dir / "setup-terminal-provider.sh")

    render_log = tmp_path / "render.log"
    xdg_config_home = _create_terminal_profile(
        tmp_path,
        "#!/usr/bin/env bash\n"
        f"echo \"$@\" > '{render_log}'\n",
    )
    bin_dir = _create_minimal_bin(tmp_path, include_kitty=True)
    host_overrides = xdg_config_home / "tino" / "host-overrides.sh"

    env = os.environ.copy()
    env.update(
        {
            "XDG_CONFIG_HOME": str(xdg_config_home),
            "PATH": str(bin_dir),
            "TINO_TERMINAL_PERSIST_FALLBACK": "1",
        }
    )

    result = subprocess.run(
        ["/bin/bash", "scripts/setup-terminal-provider.sh", "ghostty"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert render_log.read_text().strip() == "kitty " + str(repo)
    assert 'export TINO_TERMINAL_PROVIDER="kitty"' in host_overrides.read_text(encoding="utf-8")
    assert "Persisted fallback provider" in output


def test_setup_terminal_provider_prints_persist_instructions_when_requested(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir(parents=True)
    shutil.copy(repo_root / "scripts" / "setup-terminal-provider.sh", scripts_dir / "setup-terminal-provider.sh")

    xdg_config_home = _create_terminal_profile(tmp_path)
    bin_dir = _create_minimal_bin(tmp_path, include_kitty=True)

    env = os.environ.copy()
    env.update(
        {
            "XDG_CONFIG_HOME": str(xdg_config_home),
            "PATH": str(bin_dir),
            "TINO_TERMINAL_PERSIST_FALLBACK": "print",
        }
    )

    result = subprocess.run(
        ["/bin/bash", "scripts/setup-terminal-provider.sh", "ghostty"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert "Fallback provider detected (ghostty -> kitty). Persist with:" in output
    assert 'export TINO_TERMINAL_PROVIDER="kitty"' in output


def test_setup_terminal_provider_logs_compatibility_target_request(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir(parents=True)
    shutil.copy(repo_root / "scripts" / "setup-terminal-provider.sh", scripts_dir / "setup-terminal-provider.sh")

    render_log = tmp_path / "render.log"
    xdg_config_home = _create_terminal_profile(
        tmp_path,
        "#!/usr/bin/env bash\n"
        "if [[ ${1:-} == '--canonical-provider' ]]; then\n"
        "  echo ghostty\n"
        "  exit 0\n"
        "fi\n"
        f"echo \"$@\" > '{render_log}'\n",
    )
    bin_dir = _create_minimal_bin(tmp_path)
    wezterm = bin_dir / "wezterm"
    wezterm.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    wezterm.chmod(0o755)

    env = os.environ.copy()
    env.update({"XDG_CONFIG_HOME": str(xdg_config_home), "PATH": str(bin_dir)})

    result = subprocess.run(
        ["/bin/bash", "scripts/setup-terminal-provider.sh", "wezterm"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert "compatibility target requested" in output
    assert render_log.read_text().strip() == "wezterm " + str(repo)
    assert "Terminal provider configured: wezterm" in result.stdout
