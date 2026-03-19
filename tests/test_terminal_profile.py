import os
import subprocess
from pathlib import Path


def _copy_terminal_profile(tmp_path: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    profile_src = repo_root / "dotfiles" / "terminal" / ".config" / "tino" / "terminal-profile.sh"
    profile_dst = tmp_path / "terminal-profile.sh"
    profile_dst.write_text(profile_src.read_text(encoding="utf-8"), encoding="utf-8")
    profile_dst.chmod(0o755)
    return profile_dst


def test_terminal_profile_canonical_provider_defaults_to_ghostty(tmp_path: Path) -> None:
    profile = _copy_terminal_profile(tmp_path)
    result = subprocess.run(["/bin/bash", str(profile), "--canonical-provider"], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "ghostty"


def test_terminal_profile_canonical_provider_windows_host(tmp_path: Path) -> None:
    profile = _copy_terminal_profile(tmp_path)
    env = os.environ.copy()
    env.update({"OS": "Windows_NT"})
    result = subprocess.run(
        ["/bin/bash", str(profile), "--canonical-provider"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "windows-terminal"


def test_terminal_profile_preferences_prioritize_canonical_provider(tmp_path: Path) -> None:
    profile = _copy_terminal_profile(tmp_path)
    env = os.environ.copy()
    env.update({"TINO_TERMINAL_PROVIDER_PREFERENCES": "kitty,wezterm"})
    result = subprocess.run(["/bin/bash", str(profile), "--provider-preferences"], env=env, capture_output=True, text=True, check=True)
    providers = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert providers[0] == "ghostty"
    assert providers[:4] == ["ghostty", "kitty", "wezterm", "alacritty"]


def test_windows_terminal_settings_json_is_present() -> None:
    settings_path = Path(__file__).resolve().parents[1] / "windows-terminal" / "settings.json"
    assert settings_path.is_file(), "windows-terminal/settings.json should exist"


def test_terminal_profile_policy_state_classifies_wezterm_as_fallback_on_non_windows(tmp_path: Path) -> None:
    profile = _copy_terminal_profile(tmp_path)
    result = subprocess.run(["/bin/bash", str(profile), "--policy-state", "wezterm"], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "fallback"


def test_terminal_profile_host_approved_providers_match_canonical_default(tmp_path: Path) -> None:
    profile = _copy_terminal_profile(tmp_path)
    result = subprocess.run(["/bin/bash", str(profile), "--host-approved-providers"], capture_output=True, text=True, check=True)
    providers = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert providers == ["ghostty"]
