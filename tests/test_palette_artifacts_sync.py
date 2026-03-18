from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_palette_artifacts_are_in_sync() -> None:
    subprocess.run(
        [sys.executable, "scripts/helpers/generate_palette_artifacts.py", "--check"],
        cwd=REPO_ROOT,
        check=True,
    )


def test_sync_palettes_script_executes() -> None:
    subprocess.run([
        "bash",
        "scripts/helpers/sync_palettes.sh",
    ], cwd=REPO_ROOT, check=True)



def test_tmux_palette_colors_match_terminal_defaults() -> None:
    defaults_text = (REPO_ROOT / "dotfiles" / "terminal" / ".config" / "tino" / "terminal-defaults.sh").read_text(encoding="utf-8")
    tmux_text = (REPO_ROOT / "dotfiles" / "tmux" / ".tmux.palette.conf").read_text(encoding="utf-8")

    exported = {}
    for line in defaults_text.splitlines():
        if line.startswith("export TINO_TERMINAL_") and '="' in line:
            name, value = line.split('="', 1)
            exported[name.removeprefix("export ")] = value.rstrip('"')

    for color in {
        exported["TINO_TERMINAL_BACKGROUND"],
        exported["TINO_TERMINAL_FOREGROUND"],
        exported["TINO_TERMINAL_COLOR_0"],
        exported["TINO_TERMINAL_COLOR_2"],
        exported["TINO_TERMINAL_COLOR_3"],
        exported["TINO_TERMINAL_COLOR_4"],
        exported["TINO_TERMINAL_COLOR_5"],
        exported["TINO_TERMINAL_COLOR_6"],
        exported["TINO_TERMINAL_COLOR_8"],
    }:
        assert color in tmux_text, f"tmux palette file missing {color}"
