import os
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_setup_ghostty_requires_terminal_provider_entrypoint(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    shutil.copy(REPO_ROOT / "scripts" / "setup-ghostty.sh", scripts_dir / "setup-ghostty.sh")

    result = subprocess.run(
        ["/bin/bash", "scripts/setup-ghostty.sh"],
        cwd=repo,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "missing terminal provider setup" in result.stderr.lower()


def test_setup_ghostty_delegates_to_terminal_provider_with_ghostty(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    shutil.copy(REPO_ROOT / "scripts" / "setup-ghostty.sh", scripts_dir / "setup-ghostty.sh")

    provider_log = tmp_path / "provider.log"
    (scripts_dir / "setup-terminal-provider.sh").write_text(
        "#!/usr/bin/env bash\n"
        f"echo \"$@\" > '{provider_log}'\n",
        encoding="utf-8",
    )
    (scripts_dir / "setup-terminal-provider.sh").chmod(0o755)

    result = subprocess.run(
        ["/bin/bash", "scripts/setup-ghostty.sh"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )

    assert provider_log.read_text(encoding="utf-8").strip() == "ghostty"
    assert "Ghostty configured via setup-terminal-provider.sh." in result.stdout


def test_setup_ghostty_preserves_strictness_environment(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    shutil.copy(REPO_ROOT / "scripts" / "setup-ghostty.sh", scripts_dir / "setup-ghostty.sh")

    strict_log = tmp_path / "strict.log"
    (scripts_dir / "setup-terminal-provider.sh").write_text(
        "#!/usr/bin/env bash\n"
        f"echo \"${{TINO_TERMINAL_STRICT:-unset}}\" > '{strict_log}'\n",
        encoding="utf-8",
    )
    (scripts_dir / "setup-terminal-provider.sh").chmod(0o755)

    env = os.environ.copy()
    env["TINO_TERMINAL_STRICT"] = "0"

    subprocess.run(["/bin/bash", "scripts/setup-ghostty.sh"], cwd=repo, env=env, check=True)

    assert strict_log.read_text(encoding="utf-8").strip() == "0"


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


def test_setup_script_is_provider_wrapper_only() -> None:
    script_path = REPO_ROOT / "scripts" / "setup-ghostty.sh"
    script_contents = script_path.read_text(encoding="utf-8")

    assert 'bash "$terminal_provider_setup" ghostty' in script_contents
    assert "cargo install" not in script_contents
    assert "install_ghostty_with_pkg_manager" not in script_contents
