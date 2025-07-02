import json
import shutil
from pathlib import Path

import pytest

from scripts.thm import apply_palette


@pytest.mark.usefixtures("tmp_path")
def test_apply_palette_updates_configs(tmp_path: Path) -> None:
    pytest.importorskip("tomli_w")
    repo_root = Path(__file__).resolve().parents[1]

    dest = tmp_path / "repo"
    (dest / "windows-terminal").mkdir(parents=True)
    (dest / "palettes").mkdir()

    shutil.copy(repo_root / "starship.toml", dest / "starship.toml")
    shutil.copy(repo_root / "windows-terminal" / "settings.json", dest / "windows-terminal" / "settings.json")
    for p in (repo_root / "palettes").glob("*.toml"):
        shutil.copy(p, dest / "palettes" / p.name)

    apply_palette("dracula", dest)

    import tomllib

    data = tomllib.loads((dest / "starship.toml").read_text())
    assert data.get("palette") == "dracula"
    assert "dracula" in data.get("palettes", {})

    wt_data = json.loads((dest / "windows-terminal" / "settings.json").read_text())
    assert wt_data.get("profiles", {}).get("defaults", {}).get("colorScheme") == "Dracula"
    assert all(p.get("colorScheme") == "Dracula" for p in wt_data.get("profiles", {}).get("list", []))
    assert any(s.get("name") == "Dracula" for s in wt_data.get("schemes", []))
