import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def test_list_palettes_outputs_available_palettes(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "thm.py"
    result = subprocess.run(
        [sys.executable, str(script), "list-palettes"],
        capture_output=True,
        text=True,
        check=True,
    )
    output = result.stdout.strip().splitlines()
    assert "blacklight" in output


def test_apply_updates_configs(tmp_path):
    pytest.importorskip("tomli_w")
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "thm.py"

    dest = tmp_path / "repo"
    (dest / "windows-terminal").mkdir(parents=True)
    (dest / "palettes").mkdir()

    shutil.copy(repo_root / "starship.toml", dest / "starship.toml")
    shutil.copy(repo_root / "windows-terminal" / "settings.json", dest / "windows-terminal" / "settings.json")
    for p in (repo_root / "palettes").glob("*.toml"):
        shutil.copy(p, dest / "palettes" / p.name)

    env = os.environ.copy()
    env["THM_REPO_ROOT"] = str(dest)
    subprocess.run([
        sys.executable,
        str(script),
        "apply",
        "dracula",
    ], check=True, env=env)

    import tomllib
    data = tomllib.loads((dest / "starship.toml").read_text())
    assert data.get("palette") == "dracula"
    assert "dracula" in data.get("palettes", {})

    wt_data = json.loads((dest / "windows-terminal" / "settings.json").read_text())
    assert wt_data.get("profiles", {}).get("defaults", {}).get("colorScheme") == "Dracula"
    assert any(s.get("name") == "Dracula" for s in wt_data.get("schemes", []))


def test_apply_unknown_palette_errors(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "thm.py"

    dest = tmp_path / "repo"
    (dest / "windows-terminal").mkdir(parents=True)
    (dest / "palettes").mkdir()
    shutil.copy(repo_root / "starship.toml", dest / "starship.toml")
    shutil.copy(
        repo_root / "windows-terminal" / "settings.json",
        dest / "windows-terminal" / "settings.json",
    )

    env = os.environ.copy()
    env["THM_REPO_ROOT"] = str(dest)
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.run(
            [sys.executable, str(script), "apply", "missing"],
            check=True,
            env=env,
        )


def test_apply_missing_starship_errors(tmp_path):

    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "thm.py"

    dest = tmp_path / "repo"
    (dest / "windows-terminal").mkdir(parents=True)
    (dest / "palettes").mkdir()

    # Only copy windows-terminal settings

    shutil.copy(
        repo_root / "windows-terminal" / "settings.json",
        dest / "windows-terminal" / "settings.json",
    )
    for p in (repo_root / "palettes").glob("*.toml"):
        shutil.copy(p, dest / "palettes" / p.name)

    env = os.environ.copy()
    env["THM_REPO_ROOT"] = str(dest)
    result = subprocess.run(
        [sys.executable, str(script), "apply", "dracula"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert "starship.toml" in result.stderr


def test_apply_missing_wt_settings_errors(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "thm.py"

    dest = tmp_path / "repo"
    (dest / "windows-terminal").mkdir(parents=True)
    (dest / "palettes").mkdir()

    shutil.copy(repo_root / "starship.toml", dest / "starship.toml")
    for p in (repo_root / "palettes").glob("*.toml"):
        shutil.copy(p, dest / "palettes" / p.name)

    env = os.environ.copy()
    env["THM_REPO_ROOT"] = str(dest)
    result = subprocess.run(
        [sys.executable, str(script), "apply", "dracula"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert "windows-terminal" in result.stderr or "settings.json" in result.stderr

