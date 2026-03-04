import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "check-nvim-lockfile.py"
LOCKFILE = REPO_ROOT / "dotfiles" / "nvim" / ".config" / "nvim" / "lazy-lock.json"
PLUGINS_DIR = REPO_ROOT / "dotfiles" / "nvim" / ".config" / "nvim" / "lua" / "plugins"


def test_check_nvim_lockfile_passes_on_repo_state() -> None:
    result = subprocess.run(["python", str(SCRIPT)], capture_output=True, text=True, check=False)

    assert result.returncode == 0
    assert "Lockfile coverage OK" in result.stdout


def test_check_nvim_lockfile_fails_when_declared_plugin_missing(tmp_path: Path) -> None:
    lock_data = json.loads(LOCKFILE.read_text(encoding="utf-8"))
    lock_data.pop("nvim-cmp")

    test_lock = tmp_path / "lazy-lock.json"
    test_lock.write_text(json.dumps(lock_data), encoding="utf-8")

    result = subprocess.run(
        ["python", str(SCRIPT), "--plugins-dir", str(PLUGINS_DIR), "--lockfile", str(test_lock)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "nvim-cmp" in result.stderr
