import os
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _line_index(lines: list[str], needle: str) -> int:
    return next(index for index, line in enumerate(lines) if needle in line)


def test_migrate_shell_config_creates_fragments_backup_and_report(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "scripts" / "migrate-shell-config.sh", repo / "scripts" / "migrate-shell-config.sh")

    home = tmp_path / "home"
    home.mkdir()

    bashrc = home / ".bashrc"
    bashrc.write_text(
        """
# legacy shell config
export EDITOR=nvim
PATH="$HOME/bin:$PATH"
alias gs='git status'
function say_hi() {
  echo hi
}
bind '"\\e[A":history-search-backward'
""".strip()
        + "\n",
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["HOME"] = str(home)

    result = subprocess.run(
        ["/bin/bash", "scripts/migrate-shell-config.sh"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    target_dir = home / ".config" / "zsh"
    env_fragment = target_dir / "env.zsh"
    aliases_fragment = target_dir / "aliases.zsh"
    functions_fragment = target_dir / "functions.zsh"

    assert "export EDITOR=nvim" in env_fragment.read_text(encoding="utf-8")
    assert 'PATH="$HOME/bin:$PATH"' in env_fragment.read_text(encoding="utf-8")
    assert "alias gs='git status'" in aliases_fragment.read_text(encoding="utf-8")
    assert "function say_hi() {" in functions_fragment.read_text(encoding="utf-8")

    backup_dir = home / ".config" / "tino" / "shell-migration-backups"
    report_dir = home / ".config" / "tino"
    backups = list(backup_dir.glob("bashrc.*.bak"))
    reports = list(report_dir.glob("shell-migration-report.*.txt"))

    assert len(backups) == 1
    assert len(reports) == 1

    report = reports[0].read_text(encoding="utf-8")
    assert "Live runtime targets:" in report
    assert "bind '" in report
    assert "skipped lines: 1" in report
    assert "Migration report:" in result.stdout


def test_migrate_shell_config_refuses_to_overwrite_without_force(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "scripts" / "migrate-shell-config.sh", repo / "scripts" / "migrate-shell-config.sh")

    home = tmp_path / "home"
    (home / ".config" / "zsh").mkdir(parents=True)

    bashrc = home / ".bashrc"
    bashrc.write_text("export EDITOR=nvim\n", encoding="utf-8")

    env_fragment = home / ".config" / "zsh" / "env.zsh"
    env_fragment.write_text("existing\n", encoding="utf-8")

    env = os.environ.copy()
    env["HOME"] = str(home)

    result = subprocess.run(
        ["/bin/bash", "scripts/migrate-shell-config.sh"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "without --force" in result.stderr
    assert env_fragment.read_text(encoding="utf-8") == "existing\n"


def test_migrate_shell_config_force_overwrites_existing_fragments(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "scripts" / "migrate-shell-config.sh", repo / "scripts" / "migrate-shell-config.sh")

    home = tmp_path / "home"
    (home / ".config" / "zsh").mkdir(parents=True)

    bashrc = home / ".bashrc"
    bashrc.write_text("export EDITOR=nvim\n", encoding="utf-8")

    env_fragment = home / ".config" / "zsh" / "env.zsh"
    env_fragment.write_text("existing\n", encoding="utf-8")

    env = os.environ.copy()
    env["HOME"] = str(home)

    result = subprocess.run(
        ["/bin/bash", "scripts/migrate-shell-config.sh", "--force"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "export EDITOR=nvim" in env_fragment.read_text(encoding="utf-8")
    assert "Migrated env lines to live runtime path" in result.stdout


def test_minimal_bashrc_shim_prints_bootstrap_hint_once_when_migration_helper_missing(tmp_path: Path) -> None:
    bashrc = REPO_ROOT / "dotfiles" / "shell" / ".bashrc"

    home = tmp_path / "home"
    home.mkdir()
    env = os.environ.copy()
    env["HOME"] = str(home)

    first = subprocess.run(
        ["/bin/bash", "--rcfile", str(bashrc), "-i", "-c", "exit"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    second = subprocess.run(
        ["/bin/bash", "--rcfile", str(bashrc), "-i", "-c", "exit"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Hint: migration helper is not installed" in first.stderr
    assert "./scripts/install_common.sh" in first.stderr
    assert "Hint: migration helper is not installed" not in second.stderr


def test_minimal_bashrc_shim_uses_env_fallback_for_symlinked_rcfile(tmp_path: Path) -> None:
    custom_repo_root = tmp_path / "custom-d0ttino"
    migration_script = custom_repo_root / "scripts" / "migrate-shell-config.sh"
    migration_script.parent.mkdir(parents=True)
    migration_script.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    migration_script.chmod(0o755)

    bashrc_symlink = tmp_path / ".bashrc"
    bashrc_symlink.symlink_to(REPO_ROOT / "dotfiles" / "shell" / ".bashrc")

    home = tmp_path / "home"
    home.mkdir()
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["D0TTINO_REPO_ROOT"] = str(custom_repo_root)

    result = subprocess.run(
        ["/bin/bash", "--rcfile", str(bashrc_symlink), "-i", "-c", "exit"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Hint: migrate your legacy ~/.bashrc settings" in result.stderr
    assert str(migration_script) in result.stderr


def test_zshrc_loads_prompt_critical_env_before_starship_init() -> None:
    zshrc = REPO_ROOT / "dotfiles" / "shell" / ".zshrc"
    lines = zshrc.read_text(encoding="utf-8").splitlines()

    env_index = _line_index(lines, 'source_if_readable "$ZSH_CONFIG_DIR/env.zsh"')
    terminal_profile_index = _line_index(lines, 'source_if_readable "$HOME/.config/tino/terminal-defaults.sh"')
    host_profile_index = _line_index(lines, 'source_if_readable "$HOME/.config/tino/host-overrides.sh"')
    starship_init_index = _line_index(lines, 'eval "$(starship init zsh)"')

    assert env_index < starship_init_index
    assert terminal_profile_index < starship_init_index
    assert host_profile_index < starship_init_index


def test_zshrc_preserves_interactive_plugin_order_and_defers_zoxide() -> None:
    zshrc = REPO_ROOT / "dotfiles" / "shell" / ".zshrc"
    lines = zshrc.read_text(encoding="utf-8").splitlines()

    autosuggestions_index = _line_index(
        lines,
        'source_if_readable "$ZSH_PLUGIN_DIR/zsh-autosuggestions/zsh-autosuggestions.zsh"',
    )
    syntax_highlighting_index = _line_index(
        lines,
        'source_if_readable "$ZSH_PLUGIN_DIR/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"',
    )
    zoxide_defer_index = _line_index(lines, "tino_defer_eval 'eval \"$(zoxide init zsh)\"'")

    assert autosuggestions_index < syntax_highlighting_index
    assert syntax_highlighting_index < zoxide_defer_index
