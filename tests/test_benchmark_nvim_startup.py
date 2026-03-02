import os
import stat
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_fake_nvim(bin_dir: Path, startup_entries: list[str]) -> None:
    fake_nvim = bin_dir / "nvim"
    entries = "\n".join(startup_entries)
    fake_nvim.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
log_file=""
while (($#)); do
  case "$1" in
    --startuptime)
      log_file="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done
cat >"${log_file}" <<'LOG'
"""
        + entries
        + """
LOG
""",
        encoding="utf-8",
    )
    fake_nvim.chmod(fake_nvim.stat().st_mode | stat.S_IEXEC)


def test_benchmark_nvim_startup_generates_summary_with_max_entry(tmp_path: Path) -> None:
    script = REPO_ROOT / "scripts" / "benchmark_nvim_startup.sh"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    _write_fake_nvim(
        fake_bin,
        [
            "000.200: plugin/bootstrap",
            "004.500: plugin/colorscheme",
            "002.100: plugin/lsp",
        ],
    )

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["TOP_COUNT"] = "2"

    subprocess.run(["bash", str(script)], cwd=tmp_path, env=env, check=True)

    summary = (tmp_path / ".cache" / "tino" / "nvim-startup" / "summary.txt").read_text(encoding="utf-8")
    assert "Max startup entry (ms): 4.500" in summary
    assert "Top 2 startup entries (ms)" in summary
    assert "4.500 | plugin/colorscheme" in summary


def test_benchmark_nvim_startup_fails_on_threshold_regression(tmp_path: Path) -> None:
    script = REPO_ROOT / "scripts" / "benchmark_nvim_startup.sh"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    _write_fake_nvim(
        fake_bin,
        [
            "001.000: plugin/bootstrap",
            "007.250: plugin/lsp",
        ],
    )

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["TINO_NVIM_MAX_STARTUP_MS"] = "5"

    result = subprocess.run(["bash", str(script)], cwd=tmp_path, env=env, text=True, capture_output=True)

    assert result.returncode == 1
    assert "Startup regression detected" in result.stderr


def test_benchmark_nvim_startup_supports_legacy_threshold_env(tmp_path: Path) -> None:
    script = REPO_ROOT / "scripts" / "benchmark_nvim_startup.sh"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    _write_fake_nvim(
        fake_bin,
        [
            "001.000: plugin/bootstrap",
            "003.250: plugin/lsp",
        ],
    )

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["MAX_STARTUP_MS"] = "2"

    result = subprocess.run(["bash", str(script)], cwd=tmp_path, env=env, text=True, capture_output=True)

    assert result.returncode == 1
    assert "Startup regression detected" in result.stderr
