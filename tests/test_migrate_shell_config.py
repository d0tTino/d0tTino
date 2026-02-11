import os
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_migrate_shell_config_creates_fragments_backup_and_report(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "scripts" / "migrate-shell-config.sh", repo / "scripts" / "migrate-shell-config.sh")
    target_dir = repo / "dotfiles" / "shell" / ".config" / "zsh"
    target_dir.mkdir(parents=True)

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

    env_fragment = repo / "dotfiles" / "shell" / ".config" / "zsh" / "env.zsh"
    aliases_fragment = repo / "dotfiles" / "shell" / ".config" / "zsh" / "aliases.zsh"
    functions_fragment = repo / "dotfiles" / "shell" / ".config" / "zsh" / "functions.zsh"

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
    assert "bind '" in report
    assert "skipped lines: 1" in report
    assert "Migration report:" in result.stdout


def test_minimal_bashrc_shim_prints_migration_hint_once(tmp_path: Path) -> None:
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

    assert "Hint: migrate your legacy ~/.bashrc settings" in first.stderr
    assert "Hint: migrate your legacy ~/.bashrc settings" not in second.stderr
